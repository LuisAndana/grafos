from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class CasoUsoCreate(BaseModel):
    proyecto_id: int
    nombre: str = Field(..., min_length=1, max_length=200)
    actores: Optional[List[str]] = []
    descripcion: Optional[str] = None
    pasos: Optional[List[str]] = []


class CasoUsoUpdate(BaseModel):
    proyecto_id: Optional[int] = None
    nombre: Optional[str] = Field(None, min_length=1, max_length=200)
    actores: Optional[List[str]] = None
    descripcion: Optional[str] = None
    pasos: Optional[List[str]] = None


class CasoUsoResponse(BaseModel):
    id_caso_uso: int
    proyecto_id: int
    nombre: str
    actores: Optional[List] = []
    descripcion: Optional[str] = None
    pasos: Optional[List] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
