import re

SENTENCE_END = re.compile(r"[.!?]+(\s|$)")


async def chunk_sentences(token_stream):
    buffer = ""
    async for token in token_stream:
        buffer += token
        match = SENTENCE_END.search(buffer)
        while match:
            end = match.end()
            yield buffer[:end].strip()
            buffer = buffer[end:]
            match = SENTENCE_END.search(buffer)
    if buffer.strip():
        yield buffer.strip()
