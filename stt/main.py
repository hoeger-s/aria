import tempfile

from fastapi import FastAPI, File, UploadFile
from faster_whisper import WhisperModel

app = FastAPI()

model = WhisperModel("small", device="cuda", compute_type="int8")


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    segments, info = model.transcribe(tmp_path, language="de")
    text = " ".join(segment.text for segment in segments)

    return {"text": text.strip(), "language": info.language}
