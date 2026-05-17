from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://zrodlo:zrodlo@localhost:5432/zrodlo"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "zrodlo_openai"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "zrodlo"
    minio_secret_key: str = "zrodlo_secret_2024"
    minio_bucket: str = "zrodlo-docs"
    minio_secure: bool = False
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"


@lru_cache
def get_settings() -> WorkerSettings:
    return WorkerSettings()


settings = get_settings()
