from enum import StrEnum

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class TypDokumentu(StrEnum):
    METRYKA_CHRZTU = "metryka_chrztu"
    METRYKA_SLUBU = "metryka_slubu"
    ZASWIADCZENIE_BIERZMOWANIA = "zaswiadczenie_bierzmowania"
    ZASWIADCZENIE_KOMUNII = "zaswiadczenie_komunii"
    ZASWIADCZENIE_DO_SLUBU = "zaswiadczenie_do_slubu"
    ODPIS_ZGONU = "odpis_zgonu"
    PISMO_OGOLNE = "pismo_ogolne"
    HOMILIA = "homilia"
    OGLOSZENIA = "ogloszenia"


class StatusDokumentu(StrEnum):
    SZKIC = "szkic"
    DO_ZATWIERDZENIA = "do_zatwierdzenia"
    ZATWIERDZONY = "zatwierdzony"
    WYDANY = "wydany"
    ANULOWANY = "anulowany"


class Dokument(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "dokumenty"

    typ: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=StatusDokumentu.SZKIC, index=True
    )
    tytul: Mapped[str] = mapped_column(String(500), nullable=False)
    dane: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    tresc: Mapped[str | None] = mapped_column(Text, nullable=True)
    plik_klucz: Mapped[str | None] = mapped_column(String(500), nullable=True)
    wygenerowane_przez_ai: Mapped[bool] = mapped_column(default=False, nullable=False)
    zatwierdzone_przez: Mapped[str | None] = mapped_column(String(200), nullable=True)
