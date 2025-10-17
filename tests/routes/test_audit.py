from datetime import datetime, timedelta, timezone

from models import AuditLog, Eleicao, Usuario, db
from services.auth_service import ServiceResponse


AUTH_ADDRESS = "0x0000000000000000000000000000000000000aad"


def _auth_header(client, monkeypatch) -> dict:
    def fake_get_web3():
        return object()

    def fake_verify_signature_response(address, signature, store, web3):
        return ServiceResponse(payload={"success": True, "address": address}, status=200)

    monkeypatch.setattr("routes.auth.get_web3", fake_get_web3)
    monkeypatch.setattr("routes.auth.verify_signature_response", fake_verify_signature_response)

    response = client.post(
        "/api/auth/login",
        json={"address": AUTH_ADDRESS, "signature": "0xsignature"},
    )
    assert response.status_code == 200
    data = response.get_json()
    return {"Authorization": f"Bearer {data['token']}"}


def _seed_user_and_election():
    usuario = Usuario(endereco_wallet="0xSEEDAUDITUSER")
    now = datetime.now(timezone.utc)
    eleicao = Eleicao(
        titulo="Eleicao Auditada",
        descricao="Base para testes de auditoria",
        data_inicio=now - timedelta(days=1),
        data_fim=now + timedelta(days=1),
        ativa=True,
    )
    db.session.add(usuario)
    db.session.add(eleicao)
    db.session.flush()
    return usuario, eleicao


def _add_audit_log(usuario: Usuario, eleicao: Eleicao, acao: str, minutes_offset: int) -> AuditLog:
    timestamp = datetime.now(timezone.utc) - timedelta(minutes=minutes_offset)
    log = AuditLog(
        acao=acao,
        usuario_id=usuario.id,
        eleicao_id=eleicao.id,
        timestamp=timestamp,
        detalhes=f'{{"eleicao_id": {eleicao.id}, "descricao": "{acao.lower()}"}}',
    )
    db.session.add(log)
    return log


def test_get_audit_logs_returns_entries(client, monkeypatch):
    with client.application.app_context():
        usuario, eleicao = _seed_user_and_election()
        _add_audit_log(usuario, eleicao, "CRIAR_ELEICAO", 10)
        _add_audit_log(usuario, eleicao, "ATUALIZAR_ELEICAO", 5)
        db.session.commit()

    response = client.get("/api/audit/logs", headers=_auth_header(client, monkeypatch))
    assert response.status_code == 200
    body = response.get_json()
    assert len(body) == 2
    assert body[0]["acao"] == "ATUALIZAR_ELEICAO"


def test_get_audit_logs_returns_empty_when_no_entries(client, monkeypatch):
    response = client.get("/api/audit/logs", headers=_auth_header(client, monkeypatch))
    assert response.status_code == 200
    assert response.get_json() == []


def test_get_election_audit_logs_filters_by_election(client, monkeypatch):
    with client.application.app_context():
        usuario, eleicao = _seed_user_and_election()
        _add_audit_log(usuario, eleicao, "CRIAR_ELEICAO", 15)
        _add_audit_log(usuario, eleicao, "FINALIZAR_ELEICAO", 1)
        db.session.commit()
        election_id = eleicao.id

    response = client.get(
        f"/api/audit/eleicoes/{election_id}",
        headers=_auth_header(client, monkeypatch),
    )
    assert response.status_code == 200
    body = response.get_json()
    assert all(entry["usuario_id"] == body[0]["usuario_id"] for entry in body)
    assert {entry["acao"] for entry in body} == {"CRIAR_ELEICAO", "FINALIZAR_ELEICAO"}


def test_get_election_audit_logs_returns_404_when_election_missing(client, monkeypatch):
    response = client.get("/api/audit/eleicoes/999", headers=_auth_header(client, monkeypatch))
    assert response.status_code == 404


def test_get_election_audit_logs_returns_empty_list_when_no_matches(client, monkeypatch):
    with client.application.app_context():
        _, eleicao = _seed_user_and_election()
        db.session.commit()
        election_id = eleicao.id

    response = client.get(
        f"/api/audit/eleicoes/{election_id}",
        headers=_auth_header(client, monkeypatch),
    )
    assert response.status_code == 200
    assert response.get_json() == []
