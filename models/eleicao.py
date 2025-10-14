from . import db


class Eleicao(db.Model):
    __tablename__ = "eleicoes"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(255), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    data_inicio = db.Column(db.DateTime(timezone=True), nullable=False)
    data_fim = db.Column(db.DateTime(timezone=True), nullable=False)
    ativa = db.Column(db.Boolean, default=True)

    candidatos = db.relationship(
        "Candidato",
        back_populates="eleicao",
        cascade="all, delete-orphan",
    )
    votos = db.relationship(
        "Voto",
        back_populates="eleicao",
        cascade="all, delete-orphan",
    )
