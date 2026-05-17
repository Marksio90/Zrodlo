import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.dokumenty import StatusDokumentu, TypDokumentu


class DokumentCreate(BaseModel):
    typ: TypDokumentu
    tytul: str = Field(..., min_length=3, max_length=500)
    dane: dict = Field(default_factory=dict)
    tresc: str | None = None


class DokumentUpdate(BaseModel):
    status: StatusDokumentu | None = None
    tytul: str | None = Field(None, min_length=3, max_length=500)
    dane: dict | None = None
    tresc: str | None = None
    zatwierdzone_przez: str | None = None


class DokumentRead(DokumentCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: StatusDokumentu
    plik_klucz: str | None
    wygenerowane_przez_ai: bool
    zatwierdzone_przez: str | None
    created_at: datetime
    updated_at: datetime
