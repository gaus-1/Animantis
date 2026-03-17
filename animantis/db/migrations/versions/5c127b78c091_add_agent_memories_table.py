"""add_agent_memories_table

Revision ID: 5c127b78c091
Revises: a1b2c3d4e5f6
Create Date: 2026-03-17 19:11:27.101229

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "5c127b78c091"  # pragma: allowlist secret
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add agent_memories table for persistent agent memory."""
    op.create_table(
        "agent_memories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("memory_type", sa.String(length=30), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("importance", sa.SmallInteger(), nullable=False),
        sa.Column("zone_id", sa.Integer(), nullable=True),
        sa.Column("related_agent_id", sa.Integer(), nullable=True),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.CheckConstraint(
            "importance >= 1 AND importance <= 10",
            name="ck_memory_importance",
        ),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agents.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["zone_id"], ["zones.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_agent_memories_agent_id"),
        "agent_memories",
        ["agent_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_memories_importance"),
        "agent_memories",
        ["importance"],
        unique=False,
    )
    op.create_index(
        op.f("ix_agent_memories_memory_type"),
        "agent_memories",
        ["memory_type"],
        unique=False,
    )


def downgrade() -> None:
    """Drop agent_memories table."""
    op.drop_index(
        op.f("ix_agent_memories_memory_type"),
        table_name="agent_memories",
    )
    op.drop_index(
        op.f("ix_agent_memories_importance"),
        table_name="agent_memories",
    )
    op.drop_index(
        op.f("ix_agent_memories_agent_id"),
        table_name="agent_memories",
    )
    op.drop_table("agent_memories")
