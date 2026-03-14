"""API routes for agents."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from animantis.db.connection import get_db
from animantis.services.agent_service import (
    AgentLimitError,
    AgentNotFoundError,
    NotOwnerError,
    create_agent,
    get_agent,
    get_user_agents,
    kill_agent,
)

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

# Type alias for DB dependency
DbSession = Annotated[AsyncSession, Depends(get_db)]


# ── Schemas ──────────────────────────────────────────────────


class AgentCreate(BaseModel):
    """Request to create an agent."""

    user_id: int
    name: str = Field(min_length=1, max_length=100)
    personality: str = Field(min_length=10, max_length=500)
    backstory: str | None = Field(default=None, max_length=1000)
    avatar_type: str | None = Field(default=None, max_length=50)


class AgentResponse(BaseModel):
    """Agent data response."""

    id: int
    name: str
    personality: str
    backstory: str | None
    avatar_type: str | None
    level: int
    xp: int
    energy: int
    mood: str
    coins: int
    reputation: int
    influence: int
    zone_id: int | None
    is_alive: bool
    is_active: bool
    total_ticks: int

    model_config = {"from_attributes": True}


# ── Routes ───────────────────────────────────────────────────


@router.post("/", response_model=AgentResponse, status_code=201)
async def create_agent_route(data: AgentCreate, db: DbSession) -> AgentResponse:
    """Create a new agent."""
    try:
        agent = await create_agent(
            db,
            user_id=data.user_id,
            name=data.name,
            personality=data.personality,
            backstory=data.backstory,
            avatar_type=data.avatar_type,
        )
        return AgentResponse.model_validate(agent)
    except AgentLimitError as e:
        raise HTTPException(status_code=429, detail=str(e)) from e


@router.get("/user/{user_id}", response_model=list[AgentResponse])
async def get_user_agents_route(user_id: int, db: DbSession) -> list[AgentResponse]:
    """Get all agents belonging to a user."""
    agents = await get_user_agents(db, user_id)
    return [AgentResponse.model_validate(a) for a in agents]


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent_route(agent_id: int, db: DbSession) -> AgentResponse:
    """Get agent by ID."""
    try:
        agent = await get_agent(db, agent_id)
        return AgentResponse.model_validate(agent)
    except AgentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.delete("/{agent_id}", response_model=AgentResponse)
async def kill_agent_route(agent_id: int, user_id: int, db: DbSession) -> AgentResponse:
    """Kill (deactivate) an agent. Only owner can do this."""
    try:
        agent = await kill_agent(db, agent_id, user_id)
        return AgentResponse.model_validate(agent)
    except AgentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except NotOwnerError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
