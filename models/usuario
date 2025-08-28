from datetime import datetime
from . import db

class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    endereco_wallet = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    audit_logs = db.relationship("AuditLog", back_populates="usuario")