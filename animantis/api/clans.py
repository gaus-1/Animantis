"""API routes for clans."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from animantis.db.connection import get_db
from animantis.services.clan_service import (
    AlreadyInClanError,
    ClanNotFoundError,
    IsLeaderError,
    NotClanLeaderError,
    NotInClanError,
    create_clan,
    disband_clan,
    exile,
    get_clan,
    get_clan_members,
    join_clan,
    leave_clan,
    list_clans,
    promote,
)

router = APIRouter(prefix="/api/v1/clans", tags=["clans"])
DbSession = Annotated[AsyncSession, Depends(get_db)]


# ── Schemas ──────────────────────────────────────────────────


class ClanCreate(BaseModel):
    """Request to create a clan."""

    agent_id: int
    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class ClanResponse(BaseModel):
    """Clan data response."""

    id: int
    name: str
    description: str | None
    leader_agent_id: int | None
    member_count: int
    treasury: int
    founded_at: datetime

    model_config = {"from_attributes": True}


class ClanMemberResponse(BaseModel):
    """Clan member data."""

    id: int
    name: str
    level: int
    clan_role: str | None

    model_config = {"from_attributes": True}


class ClanActionRequest(BaseModel):
    """Request for clan actions (join, promote, exile)."""

    agent_id: int


# ── Routes ───────────────────────────────────────────────────


@router.post("/", response_model=ClanResponse, status_code=201)
async def create_clan_route(data: ClanCreate, db: DbSession) -> ClanResponse:
    """Create a new clan."""
    try:
        clan = await create_clan(
            db,
            agent_id=data.agent_id,
            name=data.name,
            description=data.description,
        )
        return ClanResponse.model_validate(clan)
    except AlreadyInClanError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.get("/", response_model=list[ClanResponse])
async def list_clans_route(
    db: DbSession,
    limit: int = 50,
    offset: int = 0,
) -> list[ClanResponse]:
    """List all clans."""
    clans = await list_clans(db, limit=limit, offset=offset)
    return [ClanResponse.model_validate(c) for c in clans]


@router.get("/{clan_id}", response_model=ClanResponse)
async def get_clan_route(clan_id: int, db: DbSession) -> ClanResponse:
    """Get clan details."""
    try:
        clan = await get_clan(db, clan_id)
        return ClanResponse.model_validate(clan)
    except ClanNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/{clan_id}/members", response_model=list[ClanMemberResponse])
async def get_members_route(clan_id: int, db: DbSession) -> list[ClanMemberResponse]:
    """Get clan members."""
    members = await get_clan_members(db, clan_id=clan_id)
    return [ClanMemberResponse.model_validate(m) for m in members]


@router.post("/{clan_id}/join", response_model=ClanResponse)
async def join_clan_route(
    clan_id: int,
    data: ClanActionRequest,
    db: DbSession,
) -> ClanResponse:
    """Join a clan."""
    try:
        clan = await join_clan(db, agent_id=data.agent_id, clan_id=clan_id)
        return ClanResponse.model_validate(clan)
    except AlreadyInClanError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except ClanNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/{clan_id}/leave", status_code=204)
async def leave_clan_route(
    clan_id: int,  # noqa: ARG001
    data: ClanActionRequest,
    db: DbSession,
) -> None:
    """Leave current clan."""
    try:
        await leave_clan(db, agent_id=data.agent_id)
    except NotInClanError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except IsLeaderError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.post("/{clan_id}/promote", response_model=ClanMemberResponse)
async def promote_route(
    clan_id: int,  # noqa: ARG001
    data: ClanActionRequest,
    db: DbSession,
    leader_id: int = 0,
) -> ClanMemberResponse:
    """Promote a member to officer."""
    try:
        agent = await promote(db, leader_id=leader_id, target_id=data.agent_id)
        return ClanMemberResponse.model_validate(agent)
    except NotClanLeaderError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.post("/{clan_id}/exile", status_code=204)
async def exile_route(
    clan_id: int,  # noqa: ARG001
    data: ClanActionRequest,
    db: DbSession,
    leader_id: int = 0,
) -> None:
    """Exile a member from the clan."""
    try:
        await exile(db, leader_id=leader_id, target_id=data.agent_id)
    except NotClanLeaderError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e


@router.delete("/{clan_id}", status_code=204)
async def disband_route(
    clan_id: int,  # noqa: ARG001
    db: DbSession,
    leader_id: int = 0,
) -> None:
    """Disband a clan. Only leader can do this."""
    try:
        await disband_clan(db, leader_id=leader_id)
    except NotClanLeaderError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except NotInClanError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
