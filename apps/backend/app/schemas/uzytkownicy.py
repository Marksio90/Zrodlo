import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.uzytkownicy import RolaUzytkownika


class UzytkownikCreate(BaseModel):
    email: EmailStr
    haslo: str = Field(..., min_length=8, max_length=200)
    imie: str = Field(..., min_length=2, max_length=100)
    nazwisko: str = Field(..., min_length=2, max_length=100)
    rola: RolaUzytkownika = RolaUzytkownika.PARAFIANIN
    parafia_id: uuid.UUID | None = None


class UzytkownikUpdate(BaseModel):
    imie: str | None = Field(None, min_length=2, max_length=100)
    nazwisko: str | None = Field(None, min_length=2, max_length=100)
    rola: RolaUzytkownika | None = None
    aktywny: bool | None = None


class UzytkownikRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    imie: str
    nazwisko: str
    rola: str
    parafia_id: uuid.UUID | None
    aktywny: bool
    ostatnie_logowanie: datetime | None
    created_at: datetime
    updated_at: datetime

    @property
    def pelne_imie(self) -> str:
        return f"{self.imie} {self.nazwisko}"


class LoginRequest(BaseModel):
    email: EmailStr
    haslo: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600 * 8
    user: UzytkownikRead


class ProboszczCreate(BaseModel):
    uzytkownik_id: uuid.UUID
    parafia_id: uuid.UUID | None = None
    numer_dekretu: str | None = None
    data_nominacji: date | None = None
    uwagi: str | None = None


class ProboszczRead(ProboszczCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    data_zakonczenia: date | None
    created_at: datetime
    updated_at: datetime


class WikariuszCreate(BaseModel):
    uzytkownik_id: uuid.UUID
    parafia_id: uuid.UUID | None = None
    specjalizacja: str | None = None
    data_nominacji: date | None = None
    uwagi: str | None = None


class WikariuszRead(WikariuszCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    data_zakonczenia: date | None
    created_at: datetime
    updated_at: datetime


class ParafianinCreate(BaseModel):
    uzytkownik_id: uuid.UUID | None = None
    parafia_id: uuid.UUID | None = None
    imie: str = Field(..., min_length=2, max_length=100)
    nazwisko: str = Field(..., min_length=2, max_length=100)
    data_urodzenia: date | None = None
    data_chrztu: date | None = None
    numer_parafialny: str | None = None
    adres: str | None = None
    telefon: str | None = None
    email: str | None = None
    uwagi: str | None = None


class ParafianinUpdate(BaseModel):
    imie: str | None = Field(None, min_length=2, max_length=100)
    nazwisko: str | None = Field(None, min_length=2, max_length=100)
    data_urodzenia: date | None = None
    data_chrztu: date | None = None
    adres: str | None = None
    telefon: str | None = None
    email: str | None = None
    uwagi: str | None = None


class ParafianinRead(ParafianinCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
