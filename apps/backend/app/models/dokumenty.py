import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin


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


class Dokument(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "dokumenty"

    parafia_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parafie.id", ondelete="SET NULL"), nullable=True, index=True
    )
    tworca_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("uzytkownicy.id", ondelete="SET NULL"), nullable=True
    )
    parafianin_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("parafianie.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    zatwierdzone_przez_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("uzytkownicy.id", ondelete="SET NULL"), nullable=True
    )
    typ: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=StatusDokumentu.SZKIC, index=True
    )
    tytul: Mapped[str] = mapped_column(String(500), nullable=False)
    dane: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    tresc: Mapped[str | None] = mapped_column(Text, nullable=True)
    plik_klucz: Mapped[str | None] = mapped_column(String(500), nullable=True)
    wygenerowane_przez_ai: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    data_zatwierdzenia: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    zatwierdzone_przez: Mapped[str | None] = mapped_column(String(200), nullable=True)

    tworca: Mapped["Uzytkownik | None"] = relationship(
        "Uzytkownik", foreign_keys=[tworca_id]
    )
    zatwierdzone_przez_uzytkownik: Mapped["Uzytkownik | None"] = relationship(
        "Uzytkownik", foreign_keys=[zatwierdzone_przez_id]
    )
    parafianin: Mapped["Parafianin | None"] = relationship(
        "Parafianin", foreign_keys=[parafianin_id]
    )


from app.models.uzytkownicy import Parafianin, Uzytkownik  # noqa: E402, F401
