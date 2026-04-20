"""API routes for user profile."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from animantis.api.deps import rate_limit_api
from animantis.db.connection import get_db
from animantis.db.models import Agent, User

router = APIRouter(
    prefix="/api/v1/user",
    tags=["user"],
    dependencies=[Depends(rate_limit_api)],
)
DbSession = Annotated[AsyncSession, Depends(get_db)]


class UserProfileResponse(BaseModel):
    """User profile data."""

    id: int
    telegram_id: int
    username: str
    plan: str
    coins: int
    agent_count: int
    created_at: str


@router.get("/{telegram_id}", response_model=UserProfileResponse)
async def get_user_profile(
    telegram_id: int,
    db: DbSession,
) -> UserProfileResponse:
    """Get user profile by telegram_id."""
    query = select(User).where(User.telegram_id == telegram_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        # Return default profile for unknown users
        return UserProfileResponse(
            id=0,
            telegram_id=telegram_id,
            username="guest",
            plan="free",
            coins=100,
            agent_count=0,
            created_at="",
        )

    # Count user's agents
    agent_count_q = select(func.count(Agent.id)).where(Agent.user_id == user.id)
    agent_count = (await db.execute(agent_count_q)).scalar() or 0

    return UserProfileResponse(
        id=user.id,
        telegram_id=user.telegram_id,
        username=user.username or f"user_{user.telegram_id}",
        plan=getattr(user, "plan", "free") or "free",
        coins=getattr(user, "coins", 100) or 100,
        agent_count=agent_count,
        created_at=str(user.created_at) if user.created_at else "",
    )
