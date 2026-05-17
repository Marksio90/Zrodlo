"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "liturgie",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("godzina", sa.Time(), nullable=False),
        sa.Column("typ", sa.String(50), nullable=False, server_default="powszednia"),
        sa.Column("miejsce", sa.String(200), nullable=False, server_default="Kościół parafialny"),
        sa.Column("uwagi", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_liturgie_data", "liturgie", ["data"])

    op.create_table(
        "intencje",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("liturgia_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("typ", sa.String(50), nullable=False, server_default="inna"),
        sa.Column("tresc", sa.Text(), nullable=False),
        sa.Column("ofiarodawca", sa.String(200), nullable=True),
        sa.Column("kwota", sa.Numeric(10, 2), nullable=True),
        sa.Column("potwierdzona", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("notatka_wewnetrzna", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["liturgia_id"], ["liturgie.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_intencje_liturgia_id", "intencje", ["liturgia_id"])

    op.create_table(
        "dokumenty",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("typ", sa.String(60), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="szkic"),
        sa.Column("tytul", sa.String(500), nullable=False),
        sa.Column("dane", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("tresc", sa.Text(), nullable=True),
        sa.Column("plik_klucz", sa.String(500), nullable=True),
        sa.Column("wygenerowane_przez_ai", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("zatwierdzone_przez", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dokumenty_typ", "dokumenty", ["typ"])
    op.create_index("ix_dokumenty_status", "dokumenty", ["status"])

    op.create_table(
        "wspolnoty",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("nazwa", sa.String(200), nullable=False),
        sa.Column("opis", sa.Text(), nullable=True),
        sa.Column("opiekun", sa.String(200), nullable=True),
        sa.Column("kontakt_email", sa.String(200), nullable=True),
        sa.Column("kontakt_telefon", sa.String(30), nullable=True),
        sa.Column("aktywna", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nazwa"),
    )

    op.create_table(
        "czlonkowie_wspolnot",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("wspolnota_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("imie", sa.String(100), nullable=False),
        sa.Column("nazwisko", sa.String(100), nullable=False),
        sa.Column("telefon", sa.String(30), nullable=True),
        sa.Column("email", sa.String(200), nullable=True),
        sa.Column("rola", sa.String(100), nullable=True),
        sa.Column("aktywny", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["wspolnota_id"], ["wspolnoty.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_czlonkowie_wspolnota_id", "czlonkowie_wspolnot", ["wspolnota_id"])

    op.create_table(
        "wydarzenia",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tytul", sa.String(300), nullable=False),
        sa.Column("opis", sa.Text(), nullable=True),
        sa.Column("data_od", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data_do", sa.DateTime(timezone=True), nullable=True),
        sa.Column("miejsce", sa.String(300), nullable=True),
        sa.Column("wspolnota_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cykliczne", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("cykl_opis", sa.String(100), nullable=True),
        sa.Column("kolor", sa.String(7), nullable=False, server_default="#3B82F6"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["wspolnota_id"], ["wspolnoty.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_wydarzenia_data_od", "wydarzenia", ["data_od"])
    op.create_index("ix_wydarzenia_wspolnota_id", "wydarzenia", ["wspolnota_id"])


def downgrade() -> None:
    op.drop_table("wydarzenia")
    op.drop_table("czlonkowie_wspolnot")
    op.drop_table("wspolnoty")
    op.drop_table("dokumenty")
    op.drop_table("intencje")
    op.drop_table("liturgie")
