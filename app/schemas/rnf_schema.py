# app/schemas/rnf_schema.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class RNFCreate(BaseModel):
    proyecto_id: int
    tipo: str = Field(..., min_length=1)
    descripcion: str = Field(..., min_length=10)
    metrica: Optional[str] = Field(None, max_length=255)


class RNFUpdate(BaseModel):
    tipo: Optional[str] = None
    descripcion: Optional[str] = Field(None, min_length=10)
    metrica: Optional[str] = None


class RNFResponse(BaseModel):
    id_rnf: int
    proyecto_id: int
    codigo: str
    tipo: str
    descripcion: str
    metrica: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RNFResumen(BaseModel):
    total: int
    por_tipo: dict  # {"Seguridad": 3, "Rendimiento": 2, ...}