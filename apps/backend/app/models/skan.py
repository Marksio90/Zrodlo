import uuid
from datetime import date

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin


class SkanDokumentu(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Zeskanowany lub wgrany dokument – przechowuje plik i wyniki OCR/AI."""

    __tablename__ = "skany_dokumentow"

    uzytkownik_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("uzytkownicy.id", ondelete="SET NULL"), nullable=True, index=True
    )
    nazwa_pliku: Mapped[str] = mapped_column(String(255), nullable=False)
    typ_pliku: Mapped[str] = mapped_column(String(10), nullable=False)   # pdf | jpg | png
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    minio_klucz: Mapped[str] = mapped_column(String(500), nullable=False)
    rozmiar_bajtow: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    # OCR
    tresc_ocr: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_status: Mapped[str] = mapped_column(String(20), nullable=False, default="oczekujacy")
    ocr_blad: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Klasyfikacja i encje
    typ_dokumentu: Mapped[str] = mapped_column(String(60), nullable=False, default="inne", index=True)
    jednostka_wystawiajaca: Mapped[str | None] = mapped_column(String(300), nullable=True)
    data_wystawienia: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    osoby: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    dane_kontaktowe: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    encje: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Organizacja
    tagi: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    notatki: Mapped[str | None] = mapped_column(Text, nullable=True)
    zarchiwizowany: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
