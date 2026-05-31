import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.subskrypcja import Plan
from app.services.subskrypcja import PLAN_LIMITY, LimityPlanu


class PlanInfo(BaseModel):
    plan: str
    nazwa: str
    opis: str
    cena_miesiac_pln: int
    max_uzytkownikow: int | None
    max_intencji_miesiac: int | None
    max_dokumentow: int | None
    max_ai_zapytan_miesiac: int | None
    ai_asystent: bool
    baza_wiedzy: bool
    komunikacja_masowa: bool
    dokumenty_ai: bool
    eksport_danych: bool
    api_integracje: bool


class SubskrypcjaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    parafia_id: uuid.UUID
    plan: str
    aktywna: bool
    okres_probny: bool
    data_rozpoczecia: datetime
    data_zakonczenia: datetime | None
    limit_uzytkownikow: int | None
    limit_intencji_miesiac: int | None
    limit_dokumentow: int | None
    limit_ai_zapytan_miesiac: int | None


class SubskrypcjaStatus(BaseModel):
    parafia_id: uuid.UUID
    plan: str
    aktywna: bool
    okres_probny: bool
    data_zakonczenia: datetime | None
    dni_do_konca: int | None
    limity: PlanInfo
    wymaga_odnowienia: bool


class TrialRequest(BaseModel):
    pass  # wystarczy samo żądanie – dane pobierane z tokenu


class SubskrypcjaCreate(BaseModel):
    """Tylko dla admina platformy – ręczne tworzenie subskrypcji."""
    parafia_id: uuid.UUID
    plan: Plan
    data_zakonczenia: datetime | None = None
    okres_probny: bool = False


def plan_info(plan_key: str) -> PlanInfo:
    limity = PLAN_LIMITY[plan_key]
    return PlanInfo(plan=plan_key, **limity.__dict__)
