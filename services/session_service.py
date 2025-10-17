from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import delete, select

from models import SessionToken, Usuario, db


@dataclass(frozen=True)
class SessionData:
    token: str
    user_id: int
    csrf_token: str
    expires_at: datetime


@dataclass(frozen=True)
class ResolvedSession:
    token: str
    user: Usuario
    csrf_token: str
    expires_at: datetime


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_dt(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class SessionStore:
    def __init__(self) -> None:
        self._session = db.session

    def _cleanup_expired(self) -> None:
        now = _utcnow()
        self._session.execute(
            delete(SessionToken).where(SessionToken.expires_at < now)
        )
        self._session.commit()

    def create(self, user_id: int) -> SessionData:
        self._cleanup_expired()
        token = secrets.token_urlsafe(32)
        csrf_token = secrets.token_urlsafe(16)
        expires_at = SessionToken.default_session_expiry()
        record = SessionToken(
            kind="session",
            session_id=token,
            user_id=user_id,
            csrf_token=csrf_token,
            expires_at=expires_at,
        )
        self._session.add(record)
        self._session.commit()
        return SessionData(token=token, user_id=user_id, csrf_token=csrf_token, expires_at=expires_at)

    def resolve(self, token: Optional[str]) -> Optional[ResolvedSession]:
        if not token:
            return None

        record = self._session.execute(
            select(SessionToken).where(
                SessionToken.kind == "session",
                SessionToken.session_id == token,
            )
        ).scalar_one_or_none()

        if record is None:
            return None

        if _normalize_dt(record.expires_at) <= _utcnow():
            self.destroy(token)
            return None

        user = self._session.get(Usuario, record.user_id)
        if user is None:
            self.destroy(token)
            return None

        return ResolvedSession(
            token=token,
            user=user,
            csrf_token=record.csrf_token or "",
            expires_at=record.expires_at,
        )

    def destroy(self, token: Optional[str]) -> None:
        if not token:
            return
        self._session.execute(
            delete(SessionToken).where(
                SessionToken.kind == "session",
                SessionToken.session_id == token,
            )
        )
        self._session.commit()

    def save_nonce(self, address: str, nonce: str) -> None:
        self._cleanup_expired()
        record = self._get_nonce_record(address)

        expires_at = SessionToken.default_nonce_expiry()
        if record is None:
            record = SessionToken(
                kind="nonce",
                session_id=secrets.token_urlsafe(24),
                address=address,
                nonce=nonce,
                expires_at=expires_at,
            )
            self._session.add(record)
        else:
            record.nonce = nonce
            record.expires_at = expires_at
        self._session.commit()

    def peek_nonce(self, address: str) -> Optional[str]:
        record = self._get_nonce_record(address)
        if record is None:
            return None
        if _normalize_dt(record.expires_at) <= _utcnow():
            self._session.execute(
                delete(SessionToken).where(SessionToken.id == record.id)
            )
            self._session.commit()
            return None
        return record.nonce

    def pop_nonce(self, address: str) -> Optional[str]:
        record = self._get_nonce_record(address)
        if record is None:
            return None
        if _normalize_dt(record.expires_at) <= _utcnow():
            self._session.execute(
                delete(SessionToken).where(SessionToken.id == record.id)
            )
            self._session.commit()
            return None
        nonce = record.nonce
        self._session.execute(delete(SessionToken).where(SessionToken.id == record.id))
        self._session.commit()
        return nonce

    def clear_nonces(self) -> None:
        self._session.execute(
            delete(SessionToken).where(SessionToken.kind == "nonce")
        )
        self._session.commit()

    def _get_nonce_record(self, address: str) -> Optional[SessionToken]:
        return self._session.execute(
            select(SessionToken).where(
                SessionToken.kind == "nonce",
                SessionToken.address == address,
            )
        ).scalar_one_or_none()


__all__ = ["SessionStore", "SessionData", "ResolvedSession"]
