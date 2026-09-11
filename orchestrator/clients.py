import json

import httpx
from persona import SYSTEM_PROMPT
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
        json={
            "model": settings.ollama_model,
            "prompt": prompt,
            "system": SYSTEM_PROMPT,
            "stream": False,
        },
    )
    response.raise_for_status()
    return response.json()["response"]


async def generate_stream(client: httpx.AsyncClient, prompt: str):
    async with client.stream(
        "POST",
        f"{settings.ollama_url}/api/generate",
        json={
            "model": settings.ollama_model,
            "prompt": prompt,
            "system": SYSTEM_PROMPT,
            "stream": True,
        },
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
        json={"text": text, "speaker": "serena", "language": "German"},
    )
    response.raise_for_status()
    return response.content


async def fetch_weather(client: httpx.AsyncClient) -> str | None:
    location = settings.weather_location
    try:
        response = await client.get(
            f"https://wttr.in/{location}?format=%C+%t&lang=de",
            timeout=5.0,
        )
        response.raise_for_status()
        return f"Aktuelles Wetter in {location}: {response.text.strip()}."
    except httpx.HTTPError:
        return None
