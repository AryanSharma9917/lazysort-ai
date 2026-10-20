from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma3:4b"
    max_file_bytes: int = 10 * 1024 * 1024
    max_extracted_chars: int = 12_000
    request_timeout_seconds: float = 120.0
    history_dir: Path = Path.home() / ".lazysort" / "history"
    upload_dir: Path = Path.cwd() / ".lazysort_uploads"
    max_upload_bytes: int = 100 * 1024 * 1024

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
