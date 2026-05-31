"""rodo consent table

Revision ID: 0006
Revises: 0005
Create Date: 2025-06-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "akceptacje_umowy_rodo",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False,
                  server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("parafia_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("parafie.id", ondelete="CASCADE"), nullable=False),
        sa.Column("zaakceptowana_przez", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("uzytkownicy.id", ondelete="SET NULL"), nullable=False),
        sa.Column("wersja", sa.String(20), nullable=False),
        sa.Column("zaakceptowano_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ip_adres", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_akceptacje_umowy_rodo_parafia_id",
                    "akceptacje_umowy_rodo", ["parafia_id"])
    op.create_index("ix_akceptacje_umowy_rodo_zaakceptowana_przez",
                    "akceptacje_umowy_rodo", ["zaakceptowana_przez"])


def downgrade() -> None:
    op.drop_index("ix_akceptacje_umowy_rodo_zaakceptowana_przez",
                  table_name="akceptacje_umowy_rodo")
    op.drop_index("ix_akceptacje_umowy_rodo_parafia_id",
                  table_name="akceptacje_umowy_rodo")
    op.drop_table("akceptacje_umowy_rodo")
