import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.ogloszenia import PriorytetOgloszenia, StatusOgloszenia


class OgloszenieCreate(BaseModel):
    parafia_id: uuid.UUID | None = None
    tytul: str = Field(..., min_length=3, max_length=300)
    tresc: str = Field(..., min_length=10)
    priorytet: PriorytetOgloszenia = PriorytetOgloszenia.NORMALNY
    data_publikacji: datetime | None = None
    data_wygasniecia: datetime | None = None


class OgloszenieUpdate(BaseModel):
    tytul: str | None = Field(None, min_length=3, max_length=300)
    tresc: str | None = None
    priorytet: PriorytetOgloszenia | None = None
    status: StatusOgloszenia | None = None
    data_publikacji: datetime | None = None
    data_wygasniecia: datetime | None = None


class OgloszenieRead(OgloszenieCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: StatusOgloszenia
    tworca_id: uuid.UUID | None
    zatwierdzone_przez_id: uuid.UUID | None
    data_zatwierdzenia: datetime | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
