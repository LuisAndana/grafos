# app/schemas/stakeholder_schema.py
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


# ─── REQUEST ───────────────────────────────────────────

class StakeholderCreate(BaseModel):
    proyecto_id: Optional[int] = None
    nombre: str = Field(..., min_length=2, max_length=150)
    rol: str = Field(..., min_length=2, max_length=150)
    tipo: str = Field(..., min_length=2)
    area: str = Field(..., min_length=2, max_length=100)
    nivel_influencia: str = Field(..., min_length=2)
    interes_sistema: str = Field(..., min_length=2)


class StakeholderUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=150)
    rol: Optional[str] = Field(None, min_length=2, max_length=150)
    tipo: Optional[str] = None
    area: Optional[str] = Field(None, min_length=2, max_length=100)
    nivel_influencia: Optional[str] = None
    interes_sistema: Optional[str] = None


# ─── RESPONSE ──────────────────────────────────────────

class StakeholderResponse(BaseModel):
    id_stake: int
    proyecto_id: Optional[int] = None
    nombre: str
    rol: str
    tipo: str
    area: str
    nivel_influencia: str
    interes_sistema: str
    created_at: datetime
    updated_at: datetime

    # Forzar que los enums se conviertan a string
    @field_validator('tipo', 'nivel_influencia', mode='before')
    @classmethod
    def enum_to_str(cls, v):
        if hasattr(v, 'value'):
            return v.value
        return str(v) if v else v

    class Config:
        from_attributes = True