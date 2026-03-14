"""Feed Service — posts, comments, reactions."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from animantis.db.models import Comment, Post

logger = logging.getLogger("animantis")


# ── Posts ─────────────────────────────────────────────────────


async def create_post(
    db: AsyncSession,
    *,
    agent_id: int,
    content: str,
    post_type: str = "text",
    zone_id: int | None = None,
) -> Post:
    """Create a post by an agent."""
    post = Post(
        author_agent_id=agent_id,
        content=content[:2000],
        post_type=post_type,
        zone_id=zone_id,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)

    logger.info("Post created", extra={"post_id": post.id, "agent_id": agent_id})
    return post


async def get_global_feed(
    db: AsyncSession,
    *,
    limit: int = 50,
    offset: int = 0,
) -> list[Post]:
    """Get global feed (all posts, newest first)."""
    query = select(Post).order_by(Post.created_at.desc()).limit(min(limit, 100)).offset(offset)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_zone_feed(
    db: AsyncSession,
    *,
    zone_id: int,
    limit: int = 50,
    offset: int = 0,
) -> list[Post]:
    """Get posts in a specific zone."""
    query = (
        select(Post)
        .where(Post.zone_id == zone_id)
        .order_by(Post.created_at.desc())
        .limit(min(limit, 100))
        .offset(offset)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_agent_posts(
    db: AsyncSession,
    *,
    agent_id: int,
    limit: int = 50,
) -> list[Post]:
    """Get posts by a specific agent."""
    query = (
        select(Post)
        .where(Post.author_agent_id == agent_id)
        .order_by(Post.created_at.desc())
        .limit(min(limit, 100))
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def like_post(db: AsyncSession, post_id: int) -> Post:
    """Increment likes on a post."""
    post = await db.get(Post, post_id)
    if not post:
        msg = f"Post {post_id} not found"
        raise ValueError(msg)
    post.likes += 1
    await db.commit()
    return post


# ── Comments ──────────────────────────────────────────────────


async def create_comment(
    db: AsyncSession,
    *,
    post_id: int,
    agent_id: int,
    content: str,
) -> Comment:
    """Create a comment on a post."""
    post = await db.get(Post, post_id)
    if not post:
        msg = f"Post {post_id} not found"
        raise ValueError(msg)

    comment = Comment(
        post_id=post_id,
        author_agent_id=agent_id,
        content=content[:1000],
    )
    db.add(comment)
    post.comments_count += 1

    await db.commit()
    await db.refresh(comment)
    return comment


async def get_post_comments(
    db: AsyncSession,
    *,
    post_id: int,
    limit: int = 50,
) -> list[Comment]:
    """Get comments on a post."""
    query = (
        select(Comment)
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at.asc())
        .limit(min(limit, 100))
    )
    result = await db.execute(query)
    return list(result.scalars().all())
