from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ollama_url: str = "http://localhost:11434"
    stt_url: str = "http://localhost:8001"
    tts_url: str = "http://localhost:8002"

    model_config = {"env_file": ".env"}


settings = Settings()
