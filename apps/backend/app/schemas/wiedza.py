import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.wiedza import KategoriaWiedzy


class NotatkaWiedzyCreate(BaseModel):
    parafia_id: uuid.UUID | None = None
    tytul: str = Field(..., min_length=3, max_length=400)
    tresc: str = Field(..., min_length=10)
    kategoria: KategoriaWiedzy = KategoriaWiedzy.INNE
    tagi: list[str] = Field(default_factory=list)
    publiczna: bool = False


class NotatkaWiedzyUpdate(BaseModel):
    tytul: str | None = Field(None, min_length=3, max_length=400)
    tresc: str | None = None
    kategoria: KategoriaWiedzy | None = None
    tagi: list[str] | None = None
    publiczna: bool | None = None


class NotatkaWiedzyRead(NotatkaWiedzyCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tworca_id: uuid.UUID | None
    qdrant_id: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
