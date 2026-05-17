import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class SkanListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nazwa_pliku: str
    typ_pliku: str
    mime_type: str
    rozmiar_bajtow: int
    typ_dokumentu: str
    jednostka_wystawiajaca: str | None
    data_wystawienia: date | None
    osoby: list
    tagi: list
    zarchiwizowany: bool
    ocr_status: str
    created_at: datetime


class SkanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nazwa_pliku: str
    typ_pliku: str
    mime_type: str
    rozmiar_bajtow: int
    tresc_ocr: str | None
    typ_dokumentu: str
    jednostka_wystawiajaca: str | None
    data_wystawienia: date | None
    osoby: list
    dane_kontaktowe: dict
    encje: dict
    tagi: list
    notatki: str | None
    zarchiwizowany: bool
    ocr_status: str
    ocr_blad: str | None
    created_at: datetime
    updated_at: datetime


class SkanUpdate(BaseModel):
    typ_dokumentu: str | None = Field(None, max_length=60)
    jednostka_wystawiajaca: str | None = Field(None, max_length=300)
    data_wystawienia: date | None = None
    tagi: list[str] | None = None
    notatki: str | None = None
