from datetime import datetime, timezone

from . import db


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Voto(db.Model):
    __tablename__ = "votos"

    id = db.Column(db.Integer, primary_key=True)
    eleicao_id = db.Column(db.Integer, db.ForeignKey("eleicoes.id", ondelete="CASCADE"), nullable=False)
    candidato_id = db.Column(db.Integer, db.ForeignKey("candidatos.id", ondelete="CASCADE"), nullable=False)
    hash_blockchain = db.Column(db.String(255), unique=True, nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), default=_utcnow)

    eleicao = db.relationship("Eleicao", back_populates="votos")
    candidato = db.relationship("Candidato", back_populates="votos")
