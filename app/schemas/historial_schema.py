from pydantic import BaseModel
from datetime import datetime
from typing import Any, Optional


class HistorialCreate(BaseModel):
    proyecto_id: int
    accion:      str
    modulo:      str
    detalles:    Optional[Any] = None
    es_snapshot: bool = False


class HistorialResponse(BaseModel):
    id_historial: int
    proyecto_id:  int
    accion:       str
    modulo:       str
    detalles:     Optional[Any] = None
    es_snapshot:  bool
    fecha:        datetime

    class Config:
        from_attributes = True
