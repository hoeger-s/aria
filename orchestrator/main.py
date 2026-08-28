from contextlib import asynccontextmanager

import httpx
from clients import generate, speak, transcribe
from fastapi import FastAPI, File, Request, UploadFile
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
async def converse(request: Request, file: UploadFile = File(...)):
    client = request.app.state.http_client

    audio_bytes = await file.read()
    text = await transcribe(client, audio_bytes, file.filename)
    answer = await generate(client, text)
    audio = await speak(client, answer)

    return Response(content=audio, media_type="audio/wav")
