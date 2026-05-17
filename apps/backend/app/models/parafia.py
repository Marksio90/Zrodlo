from datetime import date
from enum import StrEnum

from sqlalchemy import Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Parafia(Base, UUIDMixin, TimestampMixin):
    """Jednostka parafialna – rdzeń domeny."""

    __tablename__ = "parafie"

    nazwa: Mapped[str] = mapped_column(String(300), nullable=False)
    wezwanie: Mapped[str | None] = mapped_column(String(200), nullable=True)
    adres: Mapped[str] = mapped_column(String(400), nullable=False)
    miasto: Mapped[str] = mapped_column(String(100), nullable=False)
    kod_pocztowy: Mapped[str | None] = mapped_column(String(10), nullable=True)
    diecezja: Mapped[str | None] = mapped_column(String(200), nullable=True)
    dekanat: Mapped[str | None] = mapped_column(String(200), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    telefon: Mapped[str | None] = mapped_column(String(30), nullable=True)
    strona_www: Mapped[str | None] = mapped_column(String(300), nullable=True)
    nip: Mapped[str | None] = mapped_column(String(20), nullable=True)
    regon: Mapped[str | None] = mapped_column(String(20), nullable=True)
    data_erygowania: Mapped[date | None] = mapped_column(Date, nullable=True)
    aktywna: Mapped[bool] = mapped_column(default=True, nullable=False)

    uzytkownicy: Mapped[list["Uzytkownik"]] = relationship(
        "Uzytkownik", back_populates="parafia", foreign_keys="Uzytkownik.parafia_id"
    )


from app.models.uzytkownicy import Uzytkownik  # noqa: E402, F401
