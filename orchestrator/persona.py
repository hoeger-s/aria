from pathlib import Path

DEFAULT_SYSTEM_PROMPT = (
    "Du bist ein hilfreicher KI-Assistent. Antworte klar und praegnant, "
    "deine Antworten werden vorgelesen."
)

_PROMPT_PATH = Path(__file__).parent / "system_prompt.txt"


def load_system_prompt() -> str:
    if _PROMPT_PATH.exists():
        return _PROMPT_PATH.read_text(encoding="utf-8").strip()
    return DEFAULT_SYSTEM_PROMPT


SYSTEM_PROMPT = load_system_prompt()
