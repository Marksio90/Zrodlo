from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Literal["development", "production", "test"] = "development"
    secret_key: str = "zmien-mnie-w-produkcji-32-znaki!!"

    # Baza danych
    database_url: str = "postgresql+asyncpg://zrodlo:zrodlo@localhost:5432/zrodlo"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "zrodlo_dokumenty"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "zrodlo"
    minio_secret_key: str = "zrodlo_secret_2024"
    minio_bucket: str = "zrodlo-docs"
    minio_secure: bool = False

    # Ollama
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "gemma2:2b"
    ollama_timeout: int = 120

    # CORS
    cors_origins: list[str] = ["http://localhost", "http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
