"""seed zones data

Revision ID: a1b2c3d4e5f6
Revises: 15c5d2a2599d
Create Date: 2026-03-14 17:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"  # pragma: allowlist secret
down_revision: str | None = "15c5d2a2599d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Seed zones table with world data."""
    from animantis.db.seed_zones import ALL_ZONES

    zones_table = sa.table(
        "zones",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("realm", sa.String),
        sa.column("category", sa.String),
        sa.column("capacity", sa.Integer),
        sa.column("population", sa.Integer),
        sa.column("x", sa.Float),
        sa.column("y", sa.Float),
        sa.column("is_discoverable", sa.Boolean),
        sa.column("discover_req", sa.JSON),
    )

    for zone in ALL_ZONES:
        op.execute(
            zones_table.insert().values(
                id=zone["id"],
                name=zone["name"],
                realm=zone["realm"],
                category=zone.get("category"),
                capacity=zone.get("capacity", 1000),
                population=0,
                x=zone.get("x"),
                y=zone.get("y"),
                is_discoverable=zone.get("is_discoverable", True),
                discover_req=zone.get("discover_req"),
            )
        )

    # Update sequence to avoid id conflicts
    op.execute("SELECT setval('zones_id_seq', 19, true)")


def downgrade() -> None:
    """Remove seeded zones."""
    op.execute("DELETE FROM zones WHERE id <= 19")
