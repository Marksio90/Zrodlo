"""Skany dokumentów – tabela skany_dokumentow z OCR i metadanymi

Revision ID: 0004
Revises: 0003
Create Date: 2024-01-04 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "skany_dokumentow",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "uzytkownik_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("uzytkownicy.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("nazwa_pliku", sa.String(255), nullable=False),
        sa.Column("typ_pliku", sa.String(10), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("minio_klucz", sa.String(500), nullable=False),
        sa.Column("rozmiar_bajtow", sa.BigInteger, nullable=False, server_default="0"),
        # OCR
        sa.Column("tresc_ocr", sa.Text, nullable=True),
        sa.Column("ocr_status", sa.String(20), nullable=False, server_default="oczekujacy"),
        sa.Column("ocr_blad", sa.String(500), nullable=True),
        # Klasyfikacja
        sa.Column("typ_dokumentu", sa.String(60), nullable=False, server_default="inne", index=True),
        sa.Column("jednostka_wystawiajaca", sa.String(300), nullable=True),
        sa.Column("data_wystawienia", sa.Date, nullable=True, index=True),
        sa.Column("osoby", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("dane_kontaktowe", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("encje", postgresql.JSONB, nullable=False, server_default="{}"),
        # Organizacja
        sa.Column("tagi", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("notatki", sa.Text, nullable=True),
        sa.Column("zarchiwizowany", sa.Boolean, nullable=False, server_default="false", index=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, index=True),
    )

    # Indeks GIN dla wyszukiwania po tagach JSONB
    op.create_index(
        "ix_skany_dokumentow_tagi_gin",
        "skany_dokumentow",
        ["tagi"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_skany_dokumentow_tagi_gin", table_name="skany_dokumentow")
    op.drop_table("skany_dokumentow")
