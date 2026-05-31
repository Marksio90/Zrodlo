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

    # OpenAI (gpt-4o-mini domyślnie, gpt-4o dla prawa kanonicznego)
    openai_api_key: str = ""
    openai_model_simple: str = "gpt-4o-mini"
    openai_model_complex: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "zrodlo_openai"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "zrodlo"
    minio_secret_key: str = "zrodlo_secret_2024"
    minio_bucket: str = "zrodlo-docs"
    minio_secure: bool = False

    # CORS
    cors_origins: list[str] = ["http://localhost", "http://localhost:3000"]

    # SMTP (opcjonalnie – brak = logowanie do konsoli w trybie dev)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "system@parafia.pl"

    # URL frontendu (do linków w mailach)
    app_url: str = "http://localhost:3000"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    @property
    def refresh_secret(self) -> str:
        return self.secret_key + "_refresh_v1"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
