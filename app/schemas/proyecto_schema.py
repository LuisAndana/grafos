from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional


# ─────────────────────────────────────────────
# REQUEST  (lo que llega desde el frontend)
# ─────────────────────────────────────────────

class ProyectoCreate(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=200)
    codigo: str = Field(..., min_length=2, max_length=50)
    descripcion_problema: str = Field(..., min_length=10)
    objetivo_general: str = Field(..., min_length=10)
    fecha_inicio: date
    analista_responsable: str = Field(..., min_length=3, max_length=150)


class ProyectoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=3, max_length=200)
    codigo: Optional[str] = Field(None, min_length=2, max_length=50)
    descripcion_problema: Optional[str] = None
    objetivo_general: Optional[str] = None
    fecha_inicio: Optional[date] = None
    analista_responsable: Optional[str] = Field(None, min_length=3, max_length=150)


# ─────────────────────────────────────────────
# RESPONSE  (lo que devuelve la API)
# ─────────────────────────────────────────────

class ProyectoResponse(BaseModel):
    id_proyecto: int
    user_id: int
    nombre: str
    codigo: str
    descripcion_problema: str
    objetivo_general: str
    fecha_inicio: date
    analista_responsable: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True