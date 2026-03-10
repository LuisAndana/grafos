# app/schemas/negociacion_schema.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class NegociacionCreate(BaseModel):
    proyecto_id: Optional[int] = None
    nombre: str
    descripcion: str
    prioridad: Optional[str] = "Media"
    aceptado: Optional[int] = 0


class NegociacionUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    prioridad: Optional[str] = None
    aceptado: Optional[int] = None


class NegociacionResponse(BaseModel):
    id_negociacion: int
    proyecto_id: Optional[int]
    nombre: str
    descripcion: str
    prioridad: str
    aceptado: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NegociacionResumen(BaseModel):
    total: int
    aceptadas: int
    pendientes: int