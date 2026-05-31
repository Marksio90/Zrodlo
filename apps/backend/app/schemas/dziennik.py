import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class WpisDziennikCreate(BaseModel):
    typ: str = Field(..., pattern="^(przychodzace|wychodzace|wewnetrzne)$")
    data_wpisu: date
    data_pisma: date | None = None
    nadawca: str | None = Field(None, max_length=200)
    odbiorca: str | None = Field(None, max_length=200)
    przedmiot: str = Field(..., min_length=1, max_length=500)
    uwagi: str | None = None
    status: str = Field("robocze", pattern="^(robocze|zarejestrowane|wyslane|zarchiwizowane)$")
    dokument_id: uuid.UUID | None = None


class WpisDziennikUpdate(BaseModel):
    typ: str | None = Field(None, pattern="^(przychodzace|wychodzace|wewnetrzne)$")
    data_wpisu: date | None = None
    data_pisma: date | None = None
    nadawca: str | None = Field(None, max_length=200)
    odbiorca: str | None = Field(None, max_length=200)
    przedmiot: str | None = Field(None, min_length=1, max_length=500)
    uwagi: str | None = None
    status: str | None = Field(None, pattern="^(robocze|zarejestrowane|wyslane|zarchiwizowane)$")
    dokument_id: uuid.UUID | None = None


class WpisDziennikRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    parafia_id: uuid.UUID
    uzytkownik_id: uuid.UUID | None
    dokument_id: uuid.UUID | None
    rok: int
    kolejny_numer: int
    numer_pelny: str
    typ: str
    status: str
    data_wpisu: date
    data_pisma: date | None
    nadawca: str | None
    odbiorca: str | None
    przedmiot: str
    uwagi: str | None
    created_at: datetime
    updated_at: datetime


class StatystykiDziennika(BaseModel):
    rok: int
    lacznie: int
    przychodzace: int
    wychodzace: int
    wewnetrzne: int
    ostatni_numer: int
