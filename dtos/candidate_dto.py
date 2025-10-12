from typing import Optional

from pydantic import BaseModel, Field


class CreateCandidateDTO(BaseModel):
    nome: str = Field(..., min_length=1, max_length=255)


class UpdateCandidateDTO(BaseModel):
    nome: Optional[str] = Field(None, min_length=1, max_length=255)
