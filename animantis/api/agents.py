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


class AgentCommand(BaseModel):
    """Command from owner to agent."""

    user_id: int
    command: str = Field(min_length=1, max_length=300)


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


class CommandResponse(BaseModel):
    """Response after sending a command."""

    agent_id: int
    agent_name: str
    command: str
    status: str


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


@router.post("/{agent_id}/command", response_model=CommandResponse)
async def send_command_route(agent_id: int, data: AgentCommand, db: DbSession) -> CommandResponse:
    """Send a command from owner to agent.

    The command will be picked up by the tick processor on the next tick.
    """
    from animantis.db.models import AgentAction
    from animantis.llm.prompts import sanitize_text

    # Get agent
    try:
        agent = await get_agent(db, agent_id)
    except AgentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    # Check ownership
    if agent.user_id != data.user_id:
        raise HTTPException(status_code=403, detail="Only the owner can command this agent")

    if not agent.is_alive:
        raise HTTPException(status_code=400, detail="Cannot command a dead agent")

    # Sanitize and store command as action
    safe_command = sanitize_text(data.command, 300)
    action = AgentAction(
        agent_id=agent_id,
        action_type="owner_command",
        details={"command": safe_command, "source": "api", "user_id": data.user_id},
    )
    db.add(action)
    await db.commit()

    return CommandResponse(
        agent_id=agent.id,
        agent_name=agent.name,
        command=safe_command,
        status="queued",
    )
