import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin


class TypPowiadomienia(StrEnum):
    INFO = "info"
    SUKCES = "sukces"
    OSTRZEZENIE = "ostrzezenie"
    BLAD = "blad"
    INTENCJA = "intencja"
    DOKUMENT = "dokument"
    OGLOSZENIE = "ogloszenie"
    WYDARZENIE = "wydarzenie"


class Powiadomienie(Base, UUIDMixin):
    """
    Powiadomienia dla użytkownika. Immutable – brak soft delete i updated_at.
    Przeczytanie jest jedyną dopuszczalną zmianą stanu.
    """

    __tablename__ = "powiadomienia"

    odbiorca_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("uzytkownicy.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    typ: Mapped[str] = mapped_column(
        String(30), nullable=False, default=TypPowiadomienia.INFO, index=True
    )
    tytul: Mapped[str] = mapped_column(String(300), nullable=False)
    tresc: Mapped[str] = mapped_column(Text, nullable=False)
    przeczytane: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    data_przeczytania: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    referencja_tabela: Mapped[str | None] = mapped_column(String(100), nullable=True)
    referencja_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    odbiorca: Mapped["Uzytkownik"] = relationship("Uzytkownik", foreign_keys=[odbiorca_id])


from app.models.uzytkownicy import Uzytkownik  # noqa: E402, F401
