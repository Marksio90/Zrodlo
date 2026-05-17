import uuid
from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.intencje import TypIntencji, TypMszy


class LiturgiaCreate(BaseModel):
    data: date
    godzina: time
    typ: TypMszy = TypMszy.POWSZEDNIA
    miejsce: str = "Kościół parafialny"
    uwagi: str | None = None


class LiturgiaRead(LiturgiaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    parafia_id: uuid.UUID | None
    tworca_id: uuid.UUID | None
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime


class IntencjaCreate(BaseModel):
    liturgia_id: uuid.UUID | None = None
    typ: TypIntencji = TypIntencji.INNA
    tresc: str = Field(..., min_length=3, max_length=2000)
    ofiarodawca: str | None = Field(None, max_length=200)
    ofiarodawca_id: uuid.UUID | None = None
    kwota: Decimal | None = Field(None, ge=0)
    notatka_wewnetrzna: str | None = None


class IntencjaUpdate(BaseModel):
    liturgia_id: uuid.UUID | None = None
    typ: TypIntencji | None = None
    tresc: str | None = Field(None, min_length=3, max_length=2000)
    ofiarodawca: str | None = None
    ofiarodawca_id: uuid.UUID | None = None
    kwota: Decimal | None = None
    potwierdzona: bool | None = None
    notatka_wewnetrzna: str | None = None


class IntencjaRead(IntencjaCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    parafia_id: uuid.UUID | None
    tworca_id: uuid.UUID | None
    potwierdzona: bool
    potwierdzone_przez_id: uuid.UUID | None
    data_potwierdzenia: datetime | None
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime
