import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class WydarzenieCreate(BaseModel):
    tytul: str = Field(..., min_length=2, max_length=300)
    opis: str | None = None
    data_od: datetime
    data_do: datetime | None = None
    miejsce: str | None = None
    wspolnota_id: uuid.UUID | None = None
    cykliczne: bool = False
    cykl_opis: str | None = None
    kolor: str = "#3B82F6"

    @model_validator(mode="after")
    def validate_dates(self) -> "WydarzenieCreate":
        if self.data_do and self.data_do < self.data_od:
            raise ValueError("data_do musi być późniejsza niż data_od")
        return self


class WydarzenieUpdate(BaseModel):
    tytul: str | None = Field(None, min_length=2, max_length=300)
    opis: str | None = None
    data_od: datetime | None = None
    data_do: datetime | None = None
    miejsce: str | None = None
    wspolnota_id: uuid.UUID | None = None
    kolor: str | None = None


class WydarzenieRead(WydarzenieCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
