from contextlib import asynccontextmanager

import httpx
from audio import concat_wavs
from chunking import chunk_sentences
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

    audio_chunks = []
    async for sentence in chunk_sentences(generate_stream(client, prompt)):
        audio_chunks.append(await speak(client, sentence))

    return Response(content=concat_wavs(audio_chunks), media_type="audio/wav")
