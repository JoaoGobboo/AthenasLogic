from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class UpdateUserProfileDTO(BaseModel):
    nome: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = Field(None, min_length=5, max_length=255)
    bio: Optional[str] = Field(None, max_length=1024)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: Optional[str]):
        if value is None:
            return value
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("Invalid email address")
        return value


class UserResponseDTO(BaseModel):
    id: int
    endereco_wallet: str
    nome: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None


__all__ = ["UpdateUserProfileDTO", "UserResponseDTO"]
