"""Dziennik kancleryjny – rejestr korespondencji parafii."""
import uuid
from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin


class TypWpisu(StrEnum):
    PRZYCHODZACE = "przychodzace"
    WYCHODZACE = "wychodzace"
    WEWNETRZNE = "wewnetrzne"


class StatusWpisu(StrEnum):
    ROBOCZE = "robocze"
    ZAREJESTROWANE = "zarejestrowane"
    WYSLANE = "wyslane"
    ZARCHIWIZOWANE = "zarchiwizowane"


class WpisDziennika(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "dziennik_kancleryjny"

    parafia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parafie.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    uzytkownik_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("uzytkownicy.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    dokument_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dokumenty.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )

    rok: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    kolejny_numer: Mapped[int] = mapped_column(Integer, nullable=False)
    numer_pelny: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    typ: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False,
                                        server_default=StatusWpisu.ROBOCZE)

    data_wpisu: Mapped[date] = mapped_column(Date, nullable=False)
    data_pisma: Mapped[date | None] = mapped_column(Date, nullable=True)

    nadawca: Mapped[str | None] = mapped_column(String(200), nullable=True)
    odbiorca: Mapped[str | None] = mapped_column(String(200), nullable=True)
    przedmiot: Mapped[str] = mapped_column(String(500), nullable=False)
    uwagi: Mapped[str | None] = mapped_column(Text, nullable=True)
