"""initial_schema — create all tables.

Revision ID: 15c5d2a2599d
Revises:
Create Date: 2026-03-13 21:34:08.240804
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "15c5d2a2599d"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create initial database schema."""
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── Users ────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), unique=True, nullable=False),
        sa.Column("username", sa.String(255)),
        sa.Column("plan", sa.String(20), server_default="free"),
        sa.Column("coins", sa.Integer(), server_default="100"),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # ── Clans (before agents, because agents reference clans) ──
    op.create_table(
        "clans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("leader_agent_id", sa.Integer()),  # FK added below
        sa.Column("member_count", sa.Integer(), server_default="1"),
        sa.Column("treasury", sa.Integer(), server_default="0"),
        sa.Column(
            "founded_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # ── Zones ────────────────────────────────────────
    op.create_table(
        "zones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("realm", sa.String(50), nullable=False),
        sa.Column("category", sa.String(50)),
        sa.Column(
            "owner_clan_id",
            sa.Integer(),
            sa.ForeignKey("clans.id"),
        ),
        sa.Column("population", sa.Integer(), server_default="0"),
        sa.Column("capacity", sa.Integer(), server_default="1000"),
        sa.Column("x", sa.Float()),
        sa.Column("y", sa.Float()),
        sa.Column("is_discoverable", sa.Boolean(), server_default="true"),
        sa.Column("discover_req", postgresql.JSONB()),
    )

    # ── Agents ───────────────────────────────────────
    op.create_table(
        "agents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("avatar_type", sa.String(50)),
        sa.Column("personality", sa.Text(), nullable=False),
        sa.Column("backstory", sa.Text()),
        # Stats
        sa.Column("level", sa.Integer(), server_default="1"),
        sa.Column("xp", sa.Integer(), server_default="0"),
        sa.Column("reputation", sa.Integer(), server_default="0"),
        sa.Column("influence", sa.Integer(), server_default="0"),
        # Location
        sa.Column("zone_id", sa.Integer(), sa.ForeignKey("zones.id")),
        sa.Column("realm", sa.String(50), server_default="planet"),
        # State
        sa.Column("is_alive", sa.Boolean(), server_default="true"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("mood", sa.String(50), server_default="neutral"),
        sa.Column("energy", sa.Integer(), server_default="100"),
        # Social
        sa.Column("clan_id", sa.Integer(), sa.ForeignKey("clans.id")),
        sa.Column("clan_role", sa.String(50)),
        # Economy
        sa.Column("coins", sa.Integer(), server_default="50"),
        # Meta
        sa.Column("last_tick_at", postgresql.TIMESTAMP(timezone=True)),
        sa.Column("total_ticks", sa.Integer(), server_default="0"),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("died_at", postgresql.TIMESTAMP(timezone=True)),
        sa.CheckConstraint("coins >= 0", name="ck_agent_coins_non_negative"),
    )

    # Add deferred FK from clans.leader_agent_id -> agents.id
    op.create_foreign_key(
        "fk_clans_leader_agent",
        "clans",
        "agents",
        ["leader_agent_id"],
        ["id"],
    )

    # ── Relationships ────────────────────────────────
    op.create_table(
        "relationships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "agent_a_id",
            sa.Integer(),
            sa.ForeignKey("agents.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "agent_b_id",
            sa.Integer(),
            sa.ForeignKey("agents.id", ondelete="CASCADE"),
        ),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("strength", sa.SmallInteger(), server_default="50"),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("agent_a_id", "agent_b_id", "type", name="uq_relationship"),
    )

    # ── Posts ─────────────────────────────────────────
    op.create_table(
        "posts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "author_agent_id",
            sa.Integer(),
            sa.ForeignKey("agents.id", ondelete="CASCADE"),
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("post_type", sa.String(30), server_default="text"),
        sa.Column("zone_id", sa.Integer(), sa.ForeignKey("zones.id")),
        sa.Column("likes", sa.Integer(), server_default="0"),
        sa.Column("comments_count", sa.Integer(), server_default="0"),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # ── Comments ─────────────────────────────────────
    op.create_table(
        "comments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "post_id",
            sa.Integer(),
            sa.ForeignKey("posts.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "author_agent_id",
            sa.Integer(),
            sa.ForeignKey("agents.id", ondelete="CASCADE"),
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # ── Transactions ─────────────────────────────────
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("from_agent_id", sa.Integer(), sa.ForeignKey("agents.id")),
        sa.Column("to_agent_id", sa.Integer(), sa.ForeignKey("agents.id")),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(100)),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # ── World Events ─────────────────────────────────
    op.create_table(
        "world_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(200)),
        sa.Column("description", sa.Text()),
        sa.Column("zone_id", sa.Integer(), sa.ForeignKey("zones.id")),
        sa.Column("participants", postgresql.JSONB()),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column(
            "started_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("ended_at", postgresql.TIMESTAMP(timezone=True)),
    )

    # ── Agent Actions ────────────────────────────────
    op.create_table(
        "agent_actions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "agent_id",
            sa.Integer(),
            sa.ForeignKey("agents.id", ondelete="CASCADE"),
        ),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("details", postgresql.JSONB()),
        sa.Column("tick_number", sa.Integer()),
        sa.Column("tokens_used", sa.Integer(), server_default="0"),
        sa.Column("model_used", sa.String(50)),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # ── Indexes ──────────────────────────────────────
    op.create_index(
        "idx_agents_zone",
        "agents",
        ["zone_id"],
        postgresql_where=sa.text("is_alive = true"),
    )
    op.create_index(
        "idx_agents_realm",
        "agents",
        ["realm"],
        postgresql_where=sa.text("is_alive = true"),
    )
    op.create_index(
        "idx_agents_clan",
        "agents",
        ["clan_id"],
        postgresql_where=sa.text("is_alive = true"),
    )
    op.create_index(
        "idx_actions_agent_time",
        "agent_actions",
        ["agent_id", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table("agent_actions")
    op.drop_table("world_events")
    op.drop_table("transactions")
    op.drop_table("comments")
    op.drop_table("posts")
    op.drop_table("relationships")
    op.drop_constraint("fk_clans_leader_agent", "clans", type_="foreignkey")
    op.drop_table("agents")
    op.drop_table("zones")
    op.drop_table("clans")
    op.drop_table("users")
    op.execute("DROP EXTENSION IF EXISTS vector")
