import uuid
from enum import StrEnum

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin


class KategoriaWiedzy(StrEnum):
    LITURGIA = "liturgia"
    DUSZPASTERSTWO = "duszpasterstwo"
    ADMINISTRACJA = "administracja"
    PRAWO_KANONICZNE = "prawo_kanoniczne"
    HISTORIA_PARAFII = "historia_parafii"
    KATECHEZA = "katecheza"
    INNE = "inne"


class NotatkaWiedzy(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """
    Baza wiedzy parafialnej – notatki liturgiczne, duszpasterskie, historyczne.
    Indeksowane semantycznie w Qdrant do wyszukiwania AI.
    """

    __tablename__ = "notatki_wiedzy"

    parafia_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("parafie.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    tytul: Mapped[str] = mapped_column(String(400), nullable=False, index=True)
    tresc: Mapped[str] = mapped_column(Text, nullable=False)
    kategoria: Mapped[str] = mapped_column(
        String(60), nullable=False, default=KategoriaWiedzy.INNE, index=True
    )
    tagi: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    publiczna: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    tworca_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("uzytkownicy.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    qdrant_id: Mapped[str | None] = mapped_column(String(36), nullable=True, unique=True)

    tworca: Mapped["Uzytkownik | None"] = relationship(
        "Uzytkownik", foreign_keys=[tworca_id]
    )


from app.models.uzytkownicy import Uzytkownik  # noqa: E402, F401
