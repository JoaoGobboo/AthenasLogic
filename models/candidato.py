from . import db


class Candidato(db.Model):
    __tablename__ = "candidatos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    eleicao_id = db.Column(db.Integer, db.ForeignKey("eleicoes.id", ondelete="CASCADE"), nullable=False)
    votos_count = db.Column(db.Integer, default=0)
    blockchain_index = db.Column(db.Integer, nullable=True, index=True)

    eleicao = db.relationship("Eleicao", back_populates="candidatos")
    votos = db.relationship(
        "Voto",
        back_populates="candidato",
        cascade="all, delete-orphan",
    )
