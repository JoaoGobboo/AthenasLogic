from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class CreateElectionDTO(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=255)
    descricao: Optional[str] = None
    data_inicio: datetime
    data_fim: datetime
    ativa: bool | None = None

    @field_validator("data_fim")
    @classmethod
    def validate_dates(cls, value: datetime, info):
        data_inicio = info.data.get("data_inicio")
        if data_inicio and value <= data_inicio:
            raise ValueError("data_fim must be after data_inicio")
        return value


class UpdateElectionDTO(BaseModel):
    titulo: Optional[str] = Field(None, min_length=1, max_length=255)
    descricao: Optional[str] = None
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None
    ativa: Optional[bool] = None

    @field_validator("data_fim")
    @classmethod
    def validate_dates(cls, value: Optional[datetime], info):
        if value is None:
            return value
        data_inicio = info.data.get("data_inicio")
        if data_inicio and value <= data_inicio:
            raise ValueError("data_fim must be after data_inicio")
        return value
