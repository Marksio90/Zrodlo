import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class UzycieWpisRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    model: str
    typ: str
    tokeny_wejscie: int
    tokeny_wyjscie: int
    koszt_usd: Decimal
    czas_ms: int | None
    created_at: datetime


class UzycieDzienne(BaseModel):
    data: str          # YYYY-MM-DD
    zapytania: int
    tokeny: int
    koszt_usd: Decimal


class UzycieModelowe(BaseModel):
    model: str
    zapytania: int
    tokeny_wejscie: int
    tokeny_wyjscie: int
    koszt_usd: Decimal


class PodsumowanieAi(BaseModel):
    miesiac: str           # YYYY-MM
    zapytania_lacznie: int
    tokeny_lacznie: int
    koszt_usd_lacznie: Decimal
    limit_zapytan: int | None
    procent_limitu: float | None
    per_model: list[UzycieModelowe]
    per_dzien: list[UzycieDzienne]


class AlertAi(BaseModel):
    poziom: str           # "ok" | "ostrzezenie" | "krytyczny"
    procent_limitu: float | None
    zapytania_w_miesiacu: int
    limit_zapytan: int | None
    wiadomosc: str
