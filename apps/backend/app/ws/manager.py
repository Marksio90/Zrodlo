"""WebSocket connection manager – zarządza połączeniami per użytkownik."""

import asyncio
import json
import logging
from collections import defaultdict

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, user_id: str, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._connections[user_id].add(ws)
        logger.debug("ws_connected", extra={"user_id": user_id})

    async def disconnect(self, user_id: str, ws: WebSocket) -> None:
        async with self._lock:
            self._connections[user_id].discard(ws)
            if not self._connections[user_id]:
                del self._connections[user_id]

    async def send(self, user_id: str, payload: dict) -> None:
        """Wyślij wiadomość do wszystkich sesji danego użytkownika."""
        text = json.dumps(payload, ensure_ascii=False, default=str)
        async with self._lock:
            sockets = set(self._connections.get(user_id, set()))
        dead: list[WebSocket] = []
        for ws in sockets:
            try:
                await ws.send_text(text)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(user_id, ws)

    async def broadcast_notification(self, user_id: str, notification: dict) -> None:
        """Wyślij zdarzenie powiadomienia."""
        await self.send(user_id, {"type": "notification", "data": notification})


ws_manager = ConnectionManager()
