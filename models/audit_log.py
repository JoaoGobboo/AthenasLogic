from datetime import datetime, timezone

from . import db


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    acao = db.Column(db.String(255), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), default=_utcnow)
    detalhes = db.Column(db.Text)

    usuario = db.relationship("Usuario", back_populates="audit_logs")
