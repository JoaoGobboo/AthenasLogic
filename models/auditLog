from datetime import datetime
from . import db

class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    acao = db.Column(db.String(255), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    detalhes = db.Column(db.Text)

    usuario = db.relationship("Usuario", back_populates="audit_logs")