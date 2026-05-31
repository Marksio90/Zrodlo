"""Multi-tenancy: dodanie parafia_id do wspolnoty i skany_dokumentow

Revision ID: 0005
Revises: 0004
Create Date: 2025-05-31 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── wspolnoty ─────────────────────────────────────────────────────────────
    op.add_column(
        "wspolnoty",
        sa.Column(
            "parafia_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("parafie.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
    )
    # Zastąp globalną unikalność nazwy unikalnym indeksem per parafia
    op.drop_constraint("wspolnoty_nazwa_key", "wspolnoty", type_="unique")
    op.create_unique_constraint(
        "uq_wspolnoty_parafia_nazwa", "wspolnoty", ["parafia_id", "nazwa"]
    )

    # ── skany_dokumentow ──────────────────────────────────────────────────────
    op.add_column(
        "skany_dokumentow",
        sa.Column(
            "parafia_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("parafie.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("skany_dokumentow", "parafia_id")

    op.drop_constraint("uq_wspolnoty_parafia_nazwa", "wspolnoty", type_="unique")
    op.create_unique_constraint("wspolnoty_nazwa_key", "wspolnoty", ["nazwa"])
    op.drop_column("wspolnoty", "parafia_id")
