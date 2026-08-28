import re

SENTENCE_END = re.compile(r"[.!?]+(\s|$)")


class SentenceChunker:
    """Sammelt Tokens, gibt vollstaendige Saetze zurueck, sobald sie erkannt werden."""

    def __init__(self):
        self._buffer = ""

    def feed(self, token: str) -> list[str]:
        self._buffer += token
        sentences = []
        match = SENTENCE_END.search(self._buffer)
        while match:
            end = match.end()
            sentences.append(self._buffer[:end].strip())
            self._buffer = self._buffer[end:]
            match = SENTENCE_END.search(self._buffer)
        return sentences

    def flush(self) -> list[str]:
        rest = self._buffer.strip()
        self._buffer = ""
        return [rest] if rest else []
