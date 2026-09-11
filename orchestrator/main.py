import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime

import httpx
from audio import concat_wavs
from chunking import SentenceChunker
from clients import fetch_weather, generate_stream, speak, transcribe
from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import Response


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient(timeout=60.0)
    yield
    await app.state.http_client.aclose()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/converse")
async def converse(
    request: Request,
    file: UploadFile | None = File(None),
    text: str | None = Form(None),
):
    if file is None and text is None:
        raise HTTPException(400, "Entweder 'file' oder 'text' muss angegeben werden")

    client = request.app.state.http_client

    if text is not None:
        prompt = text
    else:
        audio_bytes = await file.read()
        prompt = await transcribe(client, audio_bytes, file.filename)

    chunker = SentenceChunker()
    speak_tasks: list[asyncio.Task] = []

    async for token in generate_stream(client, prompt):
        print(token, end="", flush=True)  # roher Wort-fuer-Wort-Strom, Platzhalter fuer Baustein 7
        for sentence in chunker.feed(token):
            speak_tasks.append(asyncio.create_task(speak(client, sentence)))

    for sentence in chunker.flush():
        speak_tasks.append(asyncio.create_task(speak(client, sentence)))

    print()  # Zeilenumbruch nach dem letzten Token

    audio_chunks = await asyncio.gather(*speak_tasks)

    return Response(content=concat_wavs(audio_chunks), media_type="audio/wav")


async def generate_and_chunk(
    client: httpx.AsyncClient,
    prompt: str,
    sentence_queue: asyncio.Queue[str | None],
    websocket: WebSocket,
):
    chunker = SentenceChunker()
    async for token in generate_stream(client, prompt):
        await websocket.send_json({"type": "token", "content": token})
        for sentence in chunker.feed(token):
            await sentence_queue.put(sentence)
    for sentence in chunker.flush():
        await sentence_queue.put(sentence)
    await sentence_queue.put(None)


async def speak_and_send(
    client: httpx.AsyncClient,
    sentence_queue: asyncio.Queue[str | None],
    websocket: WebSocket,
):
    while True:
        sentence = await sentence_queue.get()
        if sentence is None:
            break
        audio = await speak(client, sentence)
        await websocket.send_bytes(audio)


GERMAN_WEEKDAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]


async def send_greeting(client: httpx.AsyncClient, websocket: WebSocket):
    now = datetime.now()
    date_str = f"{GERMAN_WEEKDAYS[now.weekday()]}, {now.strftime('%d.%m.%Y')}"
    time_str = now.strftime("%H:%M")

    facts = f"Aktuelles Datum: {date_str}. Aktuelle Uhrzeit: {time_str} Uhr."
    weather = await fetch_weather(client)
    if weather:
        facts += f" {weather}"

    prompt = f"{facts} Begrüße mich zum Start in deinem gewohnten Charakter und nenne mir diese Informationen."

    sentence_queue: asyncio.Queue[str | None] = asyncio.Queue()
    await asyncio.gather(
        generate_and_chunk(client, prompt, sentence_queue, websocket),
        speak_and_send(client, sentence_queue, websocket),
    )
    await websocket.send_json({"type": "response_complete"})


@app.websocket("/ws")
async def converse_ws(websocket: WebSocket):
    await websocket.accept()
    client = websocket.app.state.http_client

    try:
        await send_greeting(client, websocket)
    except WebSocketDisconnect:
        return

    while True:
        message = await websocket.receive()

        if message["type"] == "websocket.disconnect":
            break

        if message.get("bytes") is not None:
            prompt = await transcribe(client, message["bytes"], "audio.webm")
        elif message.get("text") is not None:
            payload = json.loads(message["text"])
            prompt = payload["text"]
        else:
            continue

        print(f"Prompt erhalten: {prompt!r}")

        try:
            await websocket.send_json({"type": "user_message", "content": prompt})

            sentence_queue: asyncio.Queue[str | None] = asyncio.Queue()

            await asyncio.gather(
                generate_and_chunk(client, prompt, sentence_queue, websocket),
                speak_and_send(client, sentence_queue, websocket),
            )
            await websocket.send_json({"type": "response_complete"})
        except WebSocketDisconnect:
            break
