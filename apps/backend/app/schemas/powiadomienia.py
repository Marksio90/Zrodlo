import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.powiadomienia import TypPowiadomienia


class PowiadomienieCreate(BaseModel):
    odbiorca_id: uuid.UUID
    typ: TypPowiadomienia = TypPowiadomienia.INFO
    tytul: str
    tresc: str
    referencja_tabela: str | None = None
    referencja_id: str | None = None


class PowiadomienieRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    odbiorca_id: uuid.UUID
    typ: str
    tytul: str
    tresc: str
    przeczytane: bool
    data_przeczytania: datetime | None
    referencja_tabela: str | None
    referencja_id: str | None
    created_at: datetime
