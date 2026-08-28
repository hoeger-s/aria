from contextlib import asynccontextmanager

import httpx
from clients import generate, speak, transcribe
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

    answer = await generate(client, text)
    audio = await speak(client, answer)

    return Response(content=audio, media_type="audio/wav")
