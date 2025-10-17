from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class CreateElectionDTO(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=255)
    descricao: Optional[str] = None
    data_inicio: datetime
    data_fim: datetime
    ativa: Optional[bool] = None
    candidatos: Optional[list[str]] = None

    @field_validator("data_fim")
    @classmethod
    def validate_dates(cls, value: datetime, info):
        data_inicio = info.data.get("data_inicio")
        if data_inicio and value <= data_inicio:
            raise ValueError("data_fim must be after data_inicio")
        return value

    @field_validator("candidatos")
    @classmethod
    def validate_candidates(cls, value: Optional[list[str]]):
        if value is None:
            return value
        cleaned = [candidate.strip() for candidate in value if candidate and candidate.strip()]
        if not cleaned:
            return None
        return cleaned


class UpdateElectionDTO(BaseModel):
    titulo: Optional[str] = Field(None, min_length=1, max_length=255)
    descricao: Optional[str] = None
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None
    ativa: Optional[bool] = None
    candidatos: Optional[list[str]] = None

    @field_validator("data_fim")
    @classmethod
    def validate_dates(cls, value: Optional[datetime], info):
        if value is None:
            return value
        data_inicio = info.data.get("data_inicio")
        if data_inicio and value <= data_inicio:
            raise ValueError("data_fim must be after data_inicio")
        return value

    @field_validator("candidatos")
    @classmethod
    def validate_candidates(cls, value: Optional[list[str]]):
        if value is None:
            return value
        cleaned = [candidate.strip() for candidate in value if candidate and candidate.strip()]
        if not cleaned:
            return None
        return cleaned
