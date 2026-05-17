import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.grupy import RolaWGrupie, TypGrupy


class GrupaParafialnaCreate(BaseModel):
    parafia_id: uuid.UUID | None = None
    nazwa: str = Field(..., min_length=2, max_length=200)
    opis: str | None = None
    typ: TypGrupy = TypGrupy.WSPOLNOTA
    opiekun_id: uuid.UUID | None = None
    kontakt_email: str | None = None
    kontakt_telefon: str | None = None


class GrupaParafialnaUpdate(BaseModel):
    nazwa: str | None = Field(None, min_length=2, max_length=200)
    opis: str | None = None
    typ: TypGrupy | None = None
    opiekun_id: uuid.UUID | None = None
    kontakt_email: str | None = None
    kontakt_telefon: str | None = None
    aktywna: bool | None = None


class GrupaParafialnaRead(GrupaParafialnaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    aktywna: bool
    liczba_czlonkow: int = 0
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class CzlonekGrupyCreate(BaseModel):
    parafianin_id: uuid.UUID
    rola: RolaWGrupie = RolaWGrupie.CZLONEK
    data_dolaczenia: date | None = None


class CzlonekGrupyRead(CzlonekGrupyCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    grupa_id: uuid.UUID
    aktywny: bool
    created_at: datetime
    updated_at: datetime
