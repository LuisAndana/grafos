# app/schemas/rf_schema.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class RequerimientoFuncionalCreate(BaseModel):
    """Schema para crear un nuevo requerimiento funcional"""
    proyecto_id: int
    descripcion: str = Field(..., min_length=1, max_length=500)
    actor: Optional[str] = Field(None, max_length=150)
    prioridad: str = Field(default="Media", description="Alta, Media, Baja")
    estado: str = Field(default="Borrador", description="Borrador, En progreso, Completado")

    class Config:
        # Ejemplo para la documentación
        json_schema_extra = {
            "example": {
                "proyecto_id": 1,
                "descripcion": "El usuario debe poder iniciar sesión",
                "actor": "Usuario",
                "prioridad": "Alta",
                "estado": "Borrador"
            }
        }


class RequerimientoFuncionalUpdate(BaseModel):
    """Schema para actualizar un requerimiento funcional"""
    descripcion: Optional[str] = Field(None, min_length=1, max_length=500)
    actor: Optional[str] = Field(None, max_length=150)
    prioridad: Optional[str] = Field(None, description="Alta, Media, Baja")
    estado: Optional[str] = Field(None, description="Borrador, En progreso, Completado")

    class Config:
        json_schema_extra = {
            "example": {
                "descripcion": "El usuario debe poder iniciar sesión con email",
                "actor": "Usuario autenticado",
                "prioridad": "Alta",
                "estado": "En progreso"
            }
        }


class RequerimientoFuncionalResponse(BaseModel):
    """Schema de respuesta para un requerimiento funcional"""
    id_req: int
    proyecto_id: Optional[int]
    codigo: str
    descripcion: str
    actor: Optional[str]
    prioridad: str
    estado: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id_req": 1,
                "proyecto_id": 1,
                "codigo": "RF-001",
                "descripcion": "El usuario debe poder iniciar sesión",
                "actor": "Usuario",
                "prioridad": "Alta",
                "estado": "Borrador",
                "created_at": "2026-03-09T18:59:51",
                "updated_at": "2026-03-09T18:59:51"
            }
        }


class RequerimientoFuncionalResumen(BaseModel):
    """Schema para resumen de requerimientos funcionales"""
    total: int
    completados: int
    en_progreso: int
    borradores: int

    class Config:
        json_schema_extra = {
            "example": {
                "total": 5,
                "completados": 1,
                "en_progreso": 2,
                "borradores": 2
            }
        }