from __future__ import annotations

from typing import Optional

from flask import abort
from sqlalchemy.exc import SQLAlchemyError

from dtos.user_dto import UpdateUserProfileDTO
from models import Usuario, db


def _commit_session() -> None:
    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        raise exc


def get_or_create_user(address: str) -> Usuario:
    user = db.session.query(Usuario).filter_by(endereco_wallet=address).one_or_none()
    if user:
        return user

    user = Usuario(endereco_wallet=address)
    db.session.add(user)
    _commit_session()
    return user


def get_user_by_id(user_id: int) -> Optional[Usuario]:
    return db.session.get(Usuario, user_id)


def serialize_user(user: Usuario) -> dict:
    return {
        "id": user.id,
        "endereco_wallet": user.endereco_wallet,
        "nome": user.nome,
        "email": user.email,
        "bio": user.bio,
    }


def update_user_profile(user: Usuario, dto: UpdateUserProfileDTO) -> dict:
    updated = False
    if dto.nome is not None:
        user.nome = dto.nome
        updated = True
    if dto.email is not None:
        user.email = dto.email
        updated = True
    if dto.bio is not None:
        user.bio = dto.bio
        updated = True

    if not updated:
        return serialize_user(user)

    try:
        _commit_session()
    except SQLAlchemyError as exc:
        abort(400, description=str(exc))
    return serialize_user(user)


__all__ = ["get_or_create_user", "get_user_by_id", "serialize_user", "update_user_profile"]
