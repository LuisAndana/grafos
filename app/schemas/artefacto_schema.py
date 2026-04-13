from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ArtefactoResponse(BaseModel):
    id_artefacto: int
    proyecto_id: int
    nombre: str
    categoria: str
    descripcion: Optional[str] = None
    nombre_archivo: str
    ruta_archivo: str
    tipo_mime: str
    tamanio: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
