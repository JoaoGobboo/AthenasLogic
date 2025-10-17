from __future__ import annotations

from datetime import datetime, timedelta, timezone

from . import db


_SESSION_DEFAULT_TTL = timedelta(days=1)
_NONCE_DEFAULT_TTL = timedelta(minutes=5)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SessionToken(db.Model):
    __tablename__ = "session_store"

    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(20), nullable=False, default="session", index=True)
    session_id = db.Column(db.String(128), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True, index=True)
    address = db.Column(db.String(255), nullable=True, index=True)
    nonce = db.Column(db.String(255), nullable=True)
    csrf_token = db.Column(db.String(128), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=_utcnow, nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)

    usuario = db.relationship("Usuario", back_populates="sessions")

    @classmethod
    def default_session_expiry(cls) -> datetime:
        return _utcnow() + _SESSION_DEFAULT_TTL

    @classmethod
    def default_nonce_expiry(cls) -> datetime:
        return _utcnow() + _NONCE_DEFAULT_TTL


__all__ = ["SessionToken", "_SESSION_DEFAULT_TTL", "_NONCE_DEFAULT_TTL"]
