"""subscriptions table

Revision ID: 0007
Revises: 0006
Create Date: 2025-06-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subskrypcje",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False,
                  server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("parafia_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("parafie.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan", sa.String(20), nullable=False),
        sa.Column("aktywna", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("okres_probny", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("data_rozpoczecia", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data_zakonczenia", sa.DateTime(timezone=True), nullable=True),
        sa.Column("anulowana_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("aktywowana_przez", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("uzytkownicy.id", ondelete="SET NULL"), nullable=True),
        sa.Column("limit_uzytkownikow", sa.Integer(), nullable=True),
        sa.Column("limit_intencji_miesiac", sa.Integer(), nullable=True),
        sa.Column("limit_dokumentow", sa.Integer(), nullable=True),
        sa.Column("limit_ai_zapytan_miesiac", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_subskrypcje_parafia_id", "subskrypcje", ["parafia_id"])
    op.create_index("ix_subskrypcje_plan", "subskrypcje", ["plan"])
    op.create_index("ix_subskrypcje_aktywna", "subskrypcje", ["aktywna"])


def downgrade() -> None:
    op.drop_index("ix_subskrypcje_aktywna", table_name="subskrypcje")
    op.drop_index("ix_subskrypcje_plan", table_name="subskrypcje")
    op.drop_index("ix_subskrypcje_parafia_id", table_name="subskrypcje")
    op.drop_table("subskrypcje")
