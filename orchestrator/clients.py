import json

import httpx
from settings import settings


async def transcribe(client: httpx.AsyncClient, audio_bytes: bytes, filename: str) -> str:
    response = await client.post(
        f"{settings.stt_url}/transcribe",
        files={"file": (filename, audio_bytes)},
    )
    response.raise_for_status()
    return response.json()["text"]


async def generate(client: httpx.AsyncClient, prompt: str) -> str:
    response = await client.post(
        f"{settings.ollama_url}/api/generate",
        json={"model": "qwen2.5:7b", "prompt": prompt, "stream": False},
    )
    response.raise_for_status()
    return response.json()["response"]


async def generate_stream(client: httpx.AsyncClient, prompt: str):
    async with client.stream(
        "POST",
        f"{settings.ollama_url}/api/generate",
        json={"model": "qwen2.5:7b", "prompt": prompt, "stream": True},
    ) as response:
        response.raise_for_status()
        async for line in response.aiter_lines():
            if not line:
                continue
            data = json.loads(line)
            if data.get("response"):
                yield data["response"]
            if data.get("done"):
                break


async def speak(client: httpx.AsyncClient, text: str) -> bytes:
    response = await client.post(
        f"{settings.tts_url}/speak",
        json={"text": text, "speaker": "aiden", "language": "German"},
    )
    response.raise_for_status()
    return response.content
