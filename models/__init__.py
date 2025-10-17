from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .usuario import Usuario
from .eleicao import Eleicao
from .candidato import Candidato
from .voto import Voto
from .audit_log import AuditLog
from .session_token import SessionToken

__all__ = [
    "db",
    "Usuario",
    "Eleicao",
    "Candidato",
    "Voto",
    "AuditLog",
    "SessionToken",
]
