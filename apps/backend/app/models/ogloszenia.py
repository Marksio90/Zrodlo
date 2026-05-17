import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin


class StatusOgloszenia(StrEnum):
    SZKIC = "szkic"
    ZATWIERDZONY = "zatwierdzony"
    ARCHIWALNY = "archiwalny"


class PriorytetOgloszenia(StrEnum):
    NORMALNY = "normalny"
    WAZNY = "wazny"
    PILNY = "pilny"


class Ogloszenie(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Ogłoszenia parafialne – niedzielne i okolicznościowe."""

    __tablename__ = "ogloszenia"

    parafia_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("parafie.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    tytul: Mapped[str] = mapped_column(String(300), nullable=False)
    tresc: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=StatusOgloszenia.SZKIC, index=True
    )
    priorytet: Mapped[str] = mapped_column(
        String(20), nullable=False, default=PriorytetOgloszenia.NORMALNY
    )
    data_publikacji: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    data_wygasniecia: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    tworca_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("uzytkownicy.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    zatwierdzone_przez_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("uzytkownicy.id", ondelete="SET NULL"),
        nullable=True,
    )
    data_zatwierdzenia: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    tworca: Mapped["Uzytkownik | None"] = relationship(
        "Uzytkownik", foreign_keys=[tworca_id]
    )
    zatwierdzone_przez: Mapped["Uzytkownik | None"] = relationship(
        "Uzytkownik", foreign_keys=[zatwierdzone_przez_id]
    )


from app.models.uzytkownicy import Uzytkownik  # noqa: E402, F401
