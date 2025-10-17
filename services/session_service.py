from __future__ import annotations

import secrets
from dataclasses import dataclass
from threading import Lock
from typing import Dict, Optional


@dataclass(frozen=True)
class SessionData:
    token: str
    user_id: int


class SessionStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._sessions: Dict[str, int] = {}

    def create(self, user_id: int) -> SessionData:
        token = secrets.token_urlsafe(32)
        with self._lock:
            self._sessions[token] = user_id
        return SessionData(token=token, user_id=user_id)

    def resolve(self, token: str | None) -> Optional[int]:
        if not token:
            return None
        with self._lock:
            return self._sessions.get(token)

    def destroy(self, token: str | None) -> None:
        if not token:
            return
        with self._lock:
            self._sessions.pop(token, None)

    def clear(self) -> None:
        with self._lock:
            self._sessions.clear()


__all__ = ["SessionStore", "SessionData"]
