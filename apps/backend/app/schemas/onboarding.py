import uuid
from pydantic import BaseModel


class KrokOnboarding(BaseModel):
    id: str
    tytul: str
    opis: str
    ukonczone: bool


class OnboardingStatus(BaseModel):
    parafia_id: uuid.UUID | None
    gotowy: bool
    ukonczone_kroki: int
    wszystkich_krokow: int
    kroki: list[KrokOnboarding]
