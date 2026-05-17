import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ParafiaCreate(BaseModel):
    nazwa: str = Field(..., min_length=3, max_length=300)
    wezwanie: str | None = None
    adres: str = Field(..., min_length=5)
    miasto: str = Field(..., min_length=2, max_length=100)
    kod_pocztowy: str | None = None
    diecezja: str | None = None
    dekanat: str | None = None
    email: str | None = None
    telefon: str | None = None
    strona_www: str | None = None
    nip: str | None = None
    regon: str | None = None
    data_erygowania: date | None = None


class ParafiaUpdate(BaseModel):
    nazwa: str | None = Field(None, min_length=3, max_length=300)
    wezwanie: str | None = None
    adres: str | None = None
    miasto: str | None = None
    kod_pocztowy: str | None = None
    diecezja: str | None = None
    dekanat: str | None = None
    email: str | None = None
    telefon: str | None = None
    strona_www: str | None = None


class ParafiaRead(ParafiaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    aktywna: bool
    created_at: datetime
    updated_at: datetime
