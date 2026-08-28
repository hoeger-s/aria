import asyncio
from contextlib import asynccontextmanager

import httpx
from audio import concat_wavs
from chunking import SentenceChunker
from clients import generate_stream, speak, transcribe
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient(timeout=30.0)
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
    speak_tasks: list[asyncio.Tast] = []

    async for token in generate_stream(client, prompt):
        print(token, end="", flush=True)  # roher Wort-fuer-Wort-Strom, Platzhalter fuer Baustein 7
        for sentence in chunker.feed(token):
            speak_tasks.append(asyncio.create_task(speak(client, sentence)))

    for sentence in chunker.flush():
        speak_tasks.append(asyncio.create_task(speak(client, sentence)))

    print()  # Zeilenumbruch nach dem letzten Token

    audio_chunks = await asyncio.gather(*speak_tasks)

    return Response(content=concat_wavs(audio_chunks), media_type="audio/wav")
