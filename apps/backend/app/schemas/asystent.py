import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ZrodloInfo(BaseModel):
    typ: str
    id: str | None = None
    tytul: str
    fragment: str | None = None
    score: float | None = None


class RozmowaCreate(BaseModel):
    tytul: str = Field(default="Nowa rozmowa", max_length=200)


class RozmowaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tytul: str
    created_at: datetime
    updated_at: datetime


class WiadomoscRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rozmowa_id: uuid.UUID
    rola: str
    tresc: str
    model_uzyty: str | None
    zrodla: list[dict] | None
    tokens_uzyte: int | None
    created_at: datetime


class WyslijWiadomoscRequest(BaseModel):
    tresc: str = Field(..., min_length=1, max_length=4000)
