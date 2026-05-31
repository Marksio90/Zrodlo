"""ai usage tracking table

Revision ID: 0008
Revises: 0007
Create Date: 2025-06-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_uzycia",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False,
                  server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("parafia_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("parafie.id", ondelete="SET NULL"), nullable=True),
        sa.Column("uzytkownik_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("uzytkownicy.id", ondelete="SET NULL"), nullable=True),
        sa.Column("model", sa.String(60), nullable=False),
        sa.Column("typ", sa.String(20), nullable=False),
        sa.Column("tokeny_wejscie", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tokeny_wyjscie", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("koszt_usd", sa.Numeric(12, 8), nullable=False, server_default="0"),
        sa.Column("czas_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_ai_uzycia_parafia_id", "ai_uzycia", ["parafia_id"])
    op.create_index("ix_ai_uzycia_uzytkownik_id", "ai_uzycia", ["uzytkownik_id"])
    op.create_index("ix_ai_uzycia_model", "ai_uzycia", ["model"])
    op.create_index("ix_ai_uzycia_typ", "ai_uzycia", ["typ"])
    op.create_index("ix_ai_uzycia_created_at", "ai_uzycia", ["created_at"])


def downgrade() -> None:
    for idx in ["ix_ai_uzycia_created_at", "ix_ai_uzycia_typ",
                "ix_ai_uzycia_model", "ix_ai_uzycia_uzytkownik_id",
                "ix_ai_uzycia_parafia_id"]:
        op.drop_index(idx, table_name="ai_uzycia")
    op.drop_table("ai_uzycia")
