# app/schemas/requerimiento_funcional_schema.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

# Importamos los Enum del modelo para garantizar valores exactos
from app.models.requerimiento_funcional import PrioridadReqFunc, EstadoReqFunc


class RequerimientoFuncionalCreate(BaseModel):
    proyecto_id: Optional[int] = None
    descripcion: str = Field(..., min_length=5)
    actor: Optional[str] = Field(None, max_length=150)
    prioridad: PrioridadReqFunc = PrioridadReqFunc.media
    estado: EstadoReqFunc = EstadoReqFunc.borrador


class RequerimientoFuncionalUpdate(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=5)
    actor: Optional[str] = Field(None, max_length=150)
    prioridad: Optional[PrioridadReqFunc] = None
    estado: Optional[EstadoReqFunc] = None


class RequerimientoFuncionalResponse(BaseModel):
    id_req: int
    proyecto_id: Optional[int] = None
    codigo: str
    descripcion: str
    actor: Optional[str] = None
    prioridad: str
    estado: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True