import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

AKTUALNA_WERSJA = "1.0"


class UmowaInfo(BaseModel):
    wersja: str = AKTUALNA_WERSJA
    tytul: str = "Umowa Powierzenia Przetwarzania Danych Osobowych"
    data_wejscia_w_zycie: str = "2025-06-01"
    url: str = "/rodo/umowa"


class StatusRodo(BaseModel):
    parafia_id: uuid.UUID
    zaakceptowana: bool
    wersja_zaakceptowana: str | None
    zaakceptowano_at: datetime | None
    aktualna_wersja: str = AKTUALNA_WERSJA
    wymaga_akceptacji: bool


class AkceptacjaRequest(BaseModel):
    wersja: str = Field(default=AKTUALNA_WERSJA, description="Wersja umowy do zaakceptowania")


class AkceptacjaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    parafia_id: uuid.UUID
    zaakceptowana_przez: uuid.UUID
    wersja: str
    zaakceptowano_at: datetime
    ip_adres: str | None
