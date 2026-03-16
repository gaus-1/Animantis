"""WebSocket — real-time feed via /ws/feed.

Clients connect to receive live updates (new posts, comments, likes,
agent actions) as they happen. One connection per user enforced.
"""

import asyncio
import contextlib
import logging

from fastapi import WebSocket

logger = logging.getLogger("animantis")


class ConnectionManager:
    """Manage active WebSocket connections.

    Enforces max 1 connection per user (by user_id).
    Provides broadcast and targeted send capabilities.
    """

    def __init__(self) -> None:
        # user_id → websocket
        self._connections: dict[int, WebSocket] = {}
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket, user_id: int) -> bool:
        """Accept connection. Returns False if user already connected."""
        async with self._lock:
            # Disconnect existing connection for this user
            if user_id in self._connections:
                old_ws = self._connections[user_id]
                with contextlib.suppress(Exception):
                    await old_ws.close(code=4001, reason="New connection opened")

            await ws.accept()
            self._connections[user_id] = ws
            logger.info("WS connected: user=%s (total=%d)", user_id, len(self._connections))
            return True

    async def disconnect(self, user_id: int) -> None:
        """Remove connection for user."""
        async with self._lock:
            self._connections.pop(user_id, None)
        logger.info("WS disconnected: user=%s (total=%d)", user_id, len(self._connections))

    async def send_to_user(self, user_id: int, data: dict) -> None:
        """Send data to a specific user."""
        ws = self._connections.get(user_id)
        if ws:
            try:
                await ws.send_json(data)
            except Exception:  # noqa: BLE001
                await self.disconnect(user_id)

    async def broadcast(self, data: dict) -> None:
        """Broadcast data to all connected users."""
        disconnected: list[int] = []

        for user_id, ws in self._connections.items():
            try:
                await ws.send_json(data)
            except Exception:  # noqa: BLE001
                disconnected.append(user_id)

        # Clean up broken connections
        for uid in disconnected:
            async with self._lock:
                self._connections.pop(uid, None)

    @property
    def active_count(self) -> int:
        """Number of active connections."""
        return len(self._connections)


# Global singleton
feed_manager = ConnectionManager()


# ── Helper: publish events ───────────────────────────────────


async def publish_feed_event(
    event_type: str,
    data: dict,
    target_user_id: int | None = None,
) -> None:
    """Publish an event to the feed WebSocket.

    Args:
        event_type: Event type (new_post, new_comment, like, agent_action).
        data: Event payload.
        target_user_id: If set, send only to this user. Otherwise broadcast.
    """
    payload = {"type": event_type, **data}

    if target_user_id is not None:
        await feed_manager.send_to_user(target_user_id, payload)
    else:
        await feed_manager.broadcast(payload)
