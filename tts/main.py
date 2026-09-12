import io

import soundfile as sf
from fastapi import FastAPI
from fastapi.responses import Response
from faster_qwen3_tts import FasterQwen3TTS
from pydantic import BaseModel

app = FastAPI()


@app.get("/health")
async def health():
    return {"status": "ok"}


# --- Alte Preset-Variante ---
# model = FasterQwen3TTS.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice")

# --- Neue Voice-Clone-Variante (eigene Stimme, Referenzaudio siehe voice_ref/) ---
model = FasterQwen3TTS.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-Base")

REF_AUDIO = "voice_ref/Referenz_Clip.wav"
REF_TEXT_PATH = "voice_ref/Referenz_Text.txt"
with open(REF_TEXT_PATH, encoding="utf-8") as f:
    REF_TEXT = f.read().strip()


class SpeakRequest(BaseModel):
    text: str
    speaker: str = "aiden"
    language: str = "German"


@app.post("/speak")
async def speak(request: SpeakRequest):
    # --- Alte Preset-Variante ---
    # audio_list, sr = model.generate_custom_voice(
    #     text=request.text,
    #     speaker=request.speaker,
    #     language=request.language,
    # )

    # --- Neue Voice-Clone-Variante ---
    audio_list, sr = model.generate_voice_clone(
        text=request.text,
        language=request.language,
        ref_audio=REF_AUDIO,
        ref_text=REF_TEXT,
        max_new_tokens=2048,  # Default. Obergrenze erzeugter Tokens (Audiolänge)
        min_new_tokens=2,  # Default. Untergrenze erzeugter Tokens
        temperature=0.9,  # Default. Zufallsgrad der Sample-Verteilung
        top_k=50,  # Default. Sampling nur aus den 50 wahrscheinlichsten Tokens
        top_p=1.0,  # Default. Kein zusätzliches Nucleus-Sampling (1.0 = deaktiviert)
        do_sample=False,  # Default. True = Sampling (zufällig), False = greedy/deterministisch
        repetition_penalty=1.05,  # Default. Leichte Strafe gegen Wiederholungen
        xvec_only=False,  # Default. False = ICL-Modus (Referenzaudio als Kontext, braucht ref_text), True = nur Stimmembedding (kein ref_text nötig)
        non_streaming_mode=None,  # Default. None = Bibliotheks-Standard für generate_voice_clone (löst zu False auf, schrittweise Text-Zuführung)
        append_silence=True,  # Default. Hängt 0,5s Stille an Referenzaudio an, verhindert abgeschnittenes Phonem am Übergang
    )

    audio = audio_list[0]

    buffer = io.BytesIO()
    sf.write(buffer, audio, sr, format="WAV")
    buffer.seek(0)

    return Response(content=buffer.read(), media_type="audio/wav")
