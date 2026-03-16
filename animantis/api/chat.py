"""API routes for agent chat — YandexGPT Pro conversation."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from animantis.api.deps import rate_limit_chat
from animantis.db.connection import get_db
from animantis.db.models import Agent
from animantis.llm.prompts import build_chat_prompt
from animantis.llm.router import LLMError, generate_chat
from animantis.services.agent_service import AgentNotFoundError, get_agent

logger = logging.getLogger("animantis")

router = APIRouter(
    prefix="/api/v1/chat",
    tags=["chat"],
    dependencies=[Depends(rate_limit_chat)],
)

DbSession = Annotated[AsyncSession, Depends(get_db)]


# ── Schemas ──────────────────────────────────────────────────


class ChatRequest(BaseModel):
    """Chat message from user to agent."""

    user_id: int
    message: str = Field(min_length=1, max_length=1000)


class ChatResponse(BaseModel):
    """Agent reply."""

    agent_id: int
    agent_name: str
    reply: str
    mood: str
    model: str
    tokens_used: int


# ── Route ────────────────────────────────────────────────────


@router.post("/{agent_id}", response_model=ChatResponse)
async def chat_with_agent(
    agent_id: int,
    data: ChatRequest,
    db: DbSession,
) -> ChatResponse:
    """Chat with an agent using YandexGPT Pro.

    Only the agent's owner can chat with them.
    """
    # Get agent
    try:
        agent: Agent = await get_agent(db, agent_id)
    except AgentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    # Check ownership
    if agent.user_id != data.user_id:
        raise HTTPException(status_code=403, detail="Only the owner can chat with this agent")

    # Check alive
    if not agent.is_alive:
        raise HTTPException(status_code=400, detail="Cannot chat with a dead agent")

    # Build prompt (no chat history for now — stateless)
    messages = build_chat_prompt(
        name=agent.name,
        personality=agent.personality,
        mood=agent.mood,
        level=agent.level,
        recent_memories=[],  # TODO: load from agent_actions
        chat_history=[],  # TODO: persistent chat history
        user_message=data.message,
    )

    # Call LLM
    try:
        llm_response = await generate_chat(messages)
    except LLMError as e:
        logger.exception("Chat LLM error", extra={"agent_id": agent_id})
        raise HTTPException(status_code=503, detail="AI service unavailable") from e

    return ChatResponse(
        agent_id=agent.id,
        agent_name=agent.name,
        reply=llm_response.text,
        mood=agent.mood,
        model=llm_response.model,
        tokens_used=llm_response.tokens_used,
    )
