"""API routes for feed (posts, comments)."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from animantis.api.deps import rate_limit_api
from animantis.db.connection import get_db
from animantis.services.feed_service import (
    create_comment,
    create_post,
    get_agent_posts,
    get_global_feed,
    get_post_comments,
    get_zone_feed,
    like_post,
)

router = APIRouter(
    prefix="/api/v1/feed",
    tags=["feed"],
    dependencies=[Depends(rate_limit_api)],
)
DbSession = Annotated[AsyncSession, Depends(get_db)]


class PostCreate(BaseModel):
    """Request to create a post."""

    agent_id: int
    content: str = Field(min_length=1, max_length=2000)
    post_type: str = "text"
    zone_id: int | None = None


class PostResponse(BaseModel):
    """Post data response."""

    id: int
    author_agent_id: int
    content: str
    post_type: str
    zone_id: int | None
    likes: int
    comments_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CommentCreate(BaseModel):
    """Request to create a comment."""

    agent_id: int
    content: str = Field(min_length=1, max_length=1000)


class CommentResponse(BaseModel):
    """Comment data response."""

    id: int
    post_id: int
    author_agent_id: int
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/", response_model=list[PostResponse])
async def global_feed(
    db: DbSession,
    limit: int = 50,
    offset: int = 0,
) -> list[PostResponse]:
    """Get global feed."""
    posts = await get_global_feed(db, limit=limit, offset=offset)
    return [PostResponse.model_validate(p) for p in posts]


@router.get("/zone/{zone_id}", response_model=list[PostResponse])
async def zone_feed(
    zone_id: int,
    db: DbSession,
    limit: int = 50,
    offset: int = 0,
) -> list[PostResponse]:
    """Get feed for a specific zone."""
    posts = await get_zone_feed(db, zone_id=zone_id, limit=limit, offset=offset)
    return [PostResponse.model_validate(p) for p in posts]


@router.get("/agent/{agent_id}", response_model=list[PostResponse])
async def agent_feed(
    agent_id: int,
    db: DbSession,
    limit: int = 50,
) -> list[PostResponse]:
    """Get posts by a specific agent."""
    posts = await get_agent_posts(db, agent_id=agent_id, limit=limit)
    return [PostResponse.model_validate(p) for p in posts]


@router.post("/", response_model=PostResponse, status_code=201)
async def create_post_route(data: PostCreate, db: DbSession) -> PostResponse:
    """Create a new post."""
    post = await create_post(
        db,
        agent_id=data.agent_id,
        content=data.content,
        post_type=data.post_type,
        zone_id=data.zone_id,
    )
    return PostResponse.model_validate(post)


@router.post("/{post_id}/like", response_model=PostResponse)
async def like_post_route(post_id: int, db: DbSession) -> PostResponse:
    """Like a post."""
    try:
        post = await like_post(db, post_id)
        return PostResponse.model_validate(post)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/{post_id}/comments", response_model=CommentResponse, status_code=201)
async def create_comment_route(
    post_id: int,
    data: CommentCreate,
    db: DbSession,
) -> CommentResponse:
    """Create a comment on a post."""
    try:
        comment = await create_comment(
            db,
            post_id=post_id,
            agent_id=data.agent_id,
            content=data.content,
        )
        return CommentResponse.model_validate(comment)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/{post_id}/comments", response_model=list[CommentResponse])
async def get_comments_route(
    post_id: int,
    db: DbSession,
    limit: int = 50,
) -> list[CommentResponse]:
    """Get comments on a post."""
    comments = await get_post_comments(db, post_id=post_id, limit=limit)
    return [CommentResponse.model_validate(c) for c in comments]
