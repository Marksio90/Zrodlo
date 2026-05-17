"""Rozmowy – historia czatu asystenta

Revision ID: 0003
Revises: 0002
Create Date: 2024-01-03 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rozmowy",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "uzytkownik_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("uzytkownicy.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("tytul", sa.String(200), nullable=False, server_default="Nowa rozmowa"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "wiadomosci_rozmowy",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "rozmowa_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rozmowy.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("rola", sa.String(20), nullable=False),
        sa.Column("tresc", sa.Text, nullable=False),
        sa.Column("model_uzyty", sa.String(50), nullable=True),
        sa.Column("zrodla", postgresql.JSONB, nullable=True),
        sa.Column("tokens_uzyte", sa.Integer, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("wiadomosci_rozmowy")
    op.drop_table("rozmowy")
