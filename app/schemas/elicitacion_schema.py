# app/schemas/elicitacion_schema.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# ═══════════════════════════════════════════════
# ENTREVISTAS
# ═══════════════════════════════════════════════

class EntrevistaCreate(BaseModel):
    proyecto_id: Optional[int] = None
    pregunta: str = Field(..., min_length=1)
    respuesta: Optional[str] = None
    observaciones: Optional[str] = None


class EntrevistaResponse(BaseModel):
    id_entrevista: int
    proyecto_id: Optional[int] = None
    pregunta: str
    respuesta: Optional[str] = None
    observaciones: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════
# PROCESOS
# ═══════════════════════════════════════════════

class ProcesoCreate(BaseModel):
    proyecto_id: Optional[int] = None
    nombre_proceso: str = Field(..., min_length=1, max_length=200)
    descripcion: Optional[str] = None
    problemas_detectados: Optional[str] = None


class ProcesoResponse(BaseModel):
    id_proceso: int
    proyecto_id: Optional[int] = None
    nombre_proceso: str
    descripcion: Optional[str] = None
    problemas_detectados: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════
# NECESIDADES
# ═══════════════════════════════════════════════

class NecesidadCreate(BaseModel):
    proyecto_id: Optional[int] = None
    nombre: str = Field(..., min_length=1, max_length=200)
    es_predefinida: int = 0   # 1 = checkbox del sistema, 0 = personalizada
    seleccionada: int = 0     # 1 = marcada


class NecesidadResponse(BaseModel):
    id_necesidad: int
    proyecto_id: Optional[int] = None
    nombre: str
    es_predefinida: int
    seleccionada: int
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════
# RESUMEN (para el dashboard)
# ═══════════════════════════════════════════════

class ElicitacionResumen(BaseModel):
    total_entrevistas: int
    total_procesos: int
    total_necesidades: int