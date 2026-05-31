"""dziennik kancleryjny – rejestr korespondencji

Revision ID: 0009
Revises: 0008
Create Date: 2025-06-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dziennik_kancleryjny",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False,
                  server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("parafia_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("parafie.id", ondelete="CASCADE"), nullable=False),
        sa.Column("uzytkownik_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("uzytkownicy.id", ondelete="SET NULL"), nullable=True),
        sa.Column("dokument_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("dokumenty.id", ondelete="SET NULL"), nullable=True),
        sa.Column("rok", sa.Integer(), nullable=False),
        sa.Column("kolejny_numer", sa.Integer(), nullable=False),
        sa.Column("numer_pelny", sa.String(30), nullable=False),
        sa.Column("typ", sa.String(20), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="robocze"),
        sa.Column("data_wpisu", sa.Date(), nullable=False),
        sa.Column("data_pisma", sa.Date(), nullable=True),
        sa.Column("nadawca", sa.String(200), nullable=True),
        sa.Column("odbiorca", sa.String(200), nullable=True),
        sa.Column("przedmiot", sa.String(500), nullable=False),
        sa.Column("uwagi", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_dziennik_parafia_id", "dziennik_kancleryjny", ["parafia_id"])
    op.create_index("ix_dziennik_uzytkownik_id", "dziennik_kancleryjny", ["uzytkownik_id"])
    op.create_index("ix_dziennik_dokument_id", "dziennik_kancleryjny", ["dokument_id"])
    op.create_index("ix_dziennik_rok", "dziennik_kancleryjny", ["rok"])
    op.create_index("ix_dziennik_typ", "dziennik_kancleryjny", ["typ"])
    op.create_index("ix_dziennik_numer_pelny", "dziennik_kancleryjny", ["numer_pelny"])
    op.create_index("ix_dziennik_deleted_at", "dziennik_kancleryjny", ["deleted_at"])
    # Unikalność numeru per parafia+rok
    op.create_index(
        "uq_dziennik_parafia_rok_numer",
        "dziennik_kancleryjny",
        ["parafia_id", "rok", "kolejny_numer"],
        unique=True,
    )


def downgrade() -> None:
    for idx in [
        "uq_dziennik_parafia_rok_numer",
        "ix_dziennik_deleted_at", "ix_dziennik_numer_pelny",
        "ix_dziennik_typ", "ix_dziennik_rok",
        "ix_dziennik_dokument_id", "ix_dziennik_uzytkownik_id",
        "ix_dziennik_parafia_id",
    ]:
        op.drop_index(idx, table_name="dziennik_kancleryjny")
    op.drop_table("dziennik_kancleryjny")
