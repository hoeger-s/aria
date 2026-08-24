import io

import soundfile as sf
from fastapi import FastAPI
from fastapi.responses import Response
from faster_qwen3_tts import FasterQwen3TTS
from pydantic import BaseModel

app = FastAPI()

model = FasterQwen3TTS.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice")


class SpeakRequest(BaseModel):
    text: str
    speaker: str = "aiden"
    language: str = "German"


@app.post("/speak")
async def speak(request: SpeakRequest):
    audio_list, sr = model.generate_custom_voice(
        text=request.text,
        speaker=request.speaker,
        language=request.language,
    )
    audio = audio_list[0]

    buffer = io.BytesIO()
    sf.write(buffer, audio, sr, format="WAV")
    buffer.seek(0)

    return Response(content=buffer.read(), media_type="audio/wav")
