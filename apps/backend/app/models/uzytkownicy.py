import uuid
from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin


class RolaUzytkownika(StrEnum):
    ADMIN = "admin"
    PROBOSZCZ = "proboszcz"
    WIKARIUSZ = "wikariusz"
    PARAFIANIN = "parafianin"


class Uzytkownik(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Konto użytkownika systemu. Każdy kapłan i parafianin ma jedno konto."""

    __tablename__ = "uzytkownicy"

    email: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    haslo_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    imie: Mapped[str] = mapped_column(String(100), nullable=False)
    nazwisko: Mapped[str] = mapped_column(String(100), nullable=False)
    rola: Mapped[str] = mapped_column(
        String(30), nullable=False, default=RolaUzytkownika.PARAFIANIN, index=True
    )
    parafia_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("parafie.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    aktywny: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ostatnie_logowanie: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    parafia: Mapped["Parafia | None"] = relationship(
        "Parafia", back_populates="uzytkownicy", foreign_keys=[parafia_id]
    )
    proboszcz: Mapped["Proboszcz | None"] = relationship(
        "Proboszcz", back_populates="uzytkownik", uselist=False
    )
    wikariusz: Mapped["Wikariusz | None"] = relationship(
        "Wikariusz", back_populates="uzytkownik", uselist=False
    )
    parafianin: Mapped["Parafianin | None"] = relationship(
        "Parafianin", back_populates="uzytkownik", uselist=False
    )


class Proboszcz(Base, UUIDMixin, TimestampMixin):
    """Profil proboszcza – rozszerza Uzytkownik z rolą PROBOSZCZ."""

    __tablename__ = "proboszczowie"

    uzytkownik_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("uzytkownicy.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    parafia_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("parafie.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    numer_dekretu: Mapped[str | None] = mapped_column(String(100), nullable=True)
    data_nominacji: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_zakonczenia: Mapped[date | None] = mapped_column(Date, nullable=True)
    uwagi: Mapped[str | None] = mapped_column(Text, nullable=True)

    uzytkownik: Mapped["Uzytkownik"] = relationship("Uzytkownik", back_populates="proboszcz")


class Wikariusz(Base, UUIDMixin, TimestampMixin):
    """Profil wikariusza – rozszerza Uzytkownik z rolą WIKARIUSZ."""

    __tablename__ = "wikariusze"

    uzytkownik_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("uzytkownicy.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    parafia_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("parafie.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    specjalizacja: Mapped[str | None] = mapped_column(String(200), nullable=True)
    data_nominacji: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_zakonczenia: Mapped[date | None] = mapped_column(Date, nullable=True)
    uwagi: Mapped[str | None] = mapped_column(Text, nullable=True)

    uzytkownik: Mapped["Uzytkownik"] = relationship("Uzytkownik", back_populates="wikariusz")


class Parafianin(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """
    Profil parafianina. Może istnieć bez konta (uzytkownik_id=None) –
    np. dane historyczne lub osoby nieposługujące się systemem.
    """

    __tablename__ = "parafianie"

    uzytkownik_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("uzytkownicy.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
        index=True,
    )
    parafia_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("parafie.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    imie: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    nazwisko: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    data_urodzenia: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_chrztu: Mapped[date | None] = mapped_column(Date, nullable=True)
    numer_parafialny: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True)
    adres: Mapped[str | None] = mapped_column(String(400), nullable=True)
    telefon: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    uwagi: Mapped[str | None] = mapped_column(Text, nullable=True)

    uzytkownik: Mapped["Uzytkownik | None"] = relationship(
        "Uzytkownik", back_populates="parafianin"
    )


from app.models.parafia import Parafia  # noqa: E402, F401
