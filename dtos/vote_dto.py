from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class CastVoteDTO(BaseModel):
    candidato_id: int = Field(..., ge=1)
    hash_blockchain: str = Field(..., min_length=6, max_length=255)

    @field_validator("hash_blockchain")
    @classmethod
    def normalize_hash(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("hash_blockchain cannot be empty")
        if cleaned.startswith("0X"):
            cleaned = "0x" + cleaned[2:]
        return cleaned


__all__ = ["CastVoteDTO"]
