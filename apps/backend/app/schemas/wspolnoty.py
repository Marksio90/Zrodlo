import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class WspolnotaCreate(BaseModel):
    nazwa: str = Field(..., min_length=2, max_length=200)
    opis: str | None = None
    opiekun: str | None = None
    kontakt_email: str | None = None
    kontakt_telefon: str | None = None


class WspolnotaRead(WspolnotaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    aktywna: bool
    created_at: datetime
    updated_at: datetime
    liczba_czlonkow: int = 0


class CzlonekCreate(BaseModel):
    wspolnota_id: uuid.UUID
    imie: str = Field(..., min_length=2, max_length=100)
    nazwisko: str = Field(..., min_length=2, max_length=100)
    telefon: str | None = None
    email: str | None = None
    rola: str | None = None


class CzlonekRead(CzlonekCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    aktywny: bool
    created_at: datetime
    updated_at: datetime
