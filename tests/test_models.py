from models import AuditLog, Candidato, Eleicao, Usuario, Voto


def test_model_tablenames():
    assert Usuario.__tablename__ == "usuarios"
    assert Eleicao.__tablename__ == "eleicoes"
    assert Candidato.__tablename__ == "candidatos"
    assert Voto.__tablename__ == "votos"
    assert AuditLog.__tablename__ == "audit_logs"
