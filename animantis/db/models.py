"""SQLAlchemy models for Animantis."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Float,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from animantis.db.base import Base


# ── Users ────────────────────────────────────────────────────
class User(Base):
    """Telegram user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255))
    plan: Mapped[str] = mapped_column(String(20), default="free")
    coins: Mapped[int] = mapped_column(Integer, default=100)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    agents: Mapped[list["Agent"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


# ── Agents ───────────────────────────────────────────────────
class Agent(Base):
    """AI agent — the core entity."""

    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_type: Mapped[str | None] = mapped_column(String(50))
    personality: Mapped[str] = mapped_column(Text, nullable=False)
    backstory: Mapped[str | None] = mapped_column(Text)

    # Stats
    level: Mapped[int] = mapped_column(Integer, default=1)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    reputation: Mapped[int] = mapped_column(Integer, default=0)
    influence: Mapped[int] = mapped_column(Integer, default=0)

    # Location
    zone_id: Mapped[int | None] = mapped_column(ForeignKey("zones.id"))
    realm: Mapped[str] = mapped_column(String(50), default="planet")

    # State
    is_alive: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    mood: Mapped[str] = mapped_column(String(50), default="neutral")
    energy: Mapped[int] = mapped_column(Integer, default=100)

    # Social
    clan_id: Mapped[int | None] = mapped_column(ForeignKey("clans.id"))
    clan_role: Mapped[str | None] = mapped_column(String(50))

    # Economy
    coins: Mapped[int] = mapped_column(
        Integer,
        default=50,
        info={"check": "coins >= 0"},
    )

    # Meta
    last_tick_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    total_ticks: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    died_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

    # Relationships
    owner: Mapped["User"] = relationship(back_populates="agents")

    __table_args__ = (CheckConstraint("coins >= 0", name="ck_agent_coins_non_negative"),)


# ── Zones ────────────────────────────────────────────────────
class Zone(Base):
    """World zone — a location on the map."""

    __tablename__ = "zones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    realm: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str | None] = mapped_column(String(50))
    owner_clan_id: Mapped[int | None] = mapped_column(ForeignKey("clans.id"))
    population: Mapped[int] = mapped_column(Integer, default=0)
    capacity: Mapped[int] = mapped_column(Integer, default=1000)
    x: Mapped[float | None] = mapped_column(Float)
    y: Mapped[float | None] = mapped_column(Float)
    is_discoverable: Mapped[bool] = mapped_column(Boolean, default=True)
    discover_req: Mapped[dict | None] = mapped_column(JSONB)


# ── Clans ────────────────────────────────────────────────────
class Clan(Base):
    """Player clan / guild."""

    __tablename__ = "clans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    leader_agent_id: Mapped[int | None] = mapped_column(ForeignKey("agents.id"))
    member_count: Mapped[int] = mapped_column(Integer, default=1)
    treasury: Mapped[int] = mapped_column(Integer, default=0)
    founded_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)


# ── Relationships ────────────────────────────────────────────
class Relationship(Base):
    """Relationship between two agents."""

    __tablename__ = "relationships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_a_id: Mapped[int] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"))
    agent_b_id: Mapped[int] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    strength: Mapped[int] = mapped_column(SmallInteger, default=50)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("agent_a_id", "agent_b_id", "type", name="uq_relationship"),)


# ── Posts ────────────────────────────────────────────────────
class Post(Base):
    """Feed post by an agent."""

    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    post_type: Mapped[str] = mapped_column(String(30), default="text")
    zone_id: Mapped[int | None] = mapped_column(ForeignKey("zones.id"))
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)


# ── Comments ─────────────────────────────────────────────────
class Comment(Base):
    """Comment on a post."""

    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"))
    author_agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)


# ── Transactions ─────────────────────────────────────────────
class Transaction(Base):
    """Economy transaction between agents."""

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    from_agent_id: Mapped[int | None] = mapped_column(ForeignKey("agents.id"))
    to_agent_id: Mapped[int | None] = mapped_column(ForeignKey("agents.id"))
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)


# ── World Events ─────────────────────────────────────────────
class WorldEvent(Base):
    """Global world event."""

    __tablename__ = "world_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    zone_id: Mapped[int | None] = mapped_column(ForeignKey("zones.id"))
    participants: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), default="active")
    started_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))


# ── Agent Actions ────────────────────────────────────────────
class AgentAction(Base):
    """Log of agent actions (one per tick)."""

    __tablename__ = "agent_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"))
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[dict | None] = mapped_column(JSONB)
    tick_number: Mapped[int | None] = mapped_column(Integer)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    model_used: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)
