from datetime import datetime, timezone

from . import db


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    endereco_wallet = db.Column(db.String(255), unique=True, nullable=False)
    nome = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=True)
    bio = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=_utcnow)

    audit_logs = db.relationship("AuditLog", back_populates="usuario")
    sessions = db.relationship("SessionToken", back_populates="usuario")
