from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class TipoUsuarioCreate(BaseModel):
    proyecto_id: int
    tipo: str = Field(..., min_length=1, max_length=150)
    descripcion: Optional[str] = None


class TipoUsuarioUpdate(BaseModel):
    proyecto_id: Optional[int] = None
    tipo: Optional[str] = Field(None, min_length=1, max_length=150)
    descripcion: Optional[str] = None


class TipoUsuarioResponse(BaseModel):
    id_tipo_usuario: int
    proyecto_id: int
    tipo: str
    descripcion: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
