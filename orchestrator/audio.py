import io
import wave


def concat_wavs(chunks: list[bytes]) -> bytes:
    if not chunks:
        return b""

    output = io.BytesIO()
    writer = None

    for chunk in chunks:
        with wave.open(io.BytesIO(chunk), "rb") as reader:
            if writer is None:
                writer = wave.open(output, "wb")
                writer.setnchannels(reader.getnchannels())
                writer.setsampwidth(reader.getsampwidth())
                writer.setframerate(reader.getframerate())
            writer.writeframes(reader.readframes(reader.getnframes()))

    writer.close()
    return output.getvalue()
