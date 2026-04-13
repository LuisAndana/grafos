from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class RestriccionCreate(BaseModel):
    proyecto_id: int
    codigo: str = Field(..., min_length=1, max_length=50)
    tipo: str = Field(..., min_length=1, max_length=100)
    descripcion: Optional[str] = None


class RestriccionUpdate(BaseModel):
    proyecto_id: Optional[int] = None
    codigo: Optional[str] = Field(None, min_length=1, max_length=50)
    tipo: Optional[str] = Field(None, min_length=1, max_length=100)
    descripcion: Optional[str] = None


class RestriccionResponse(BaseModel):
    id_restriccion: int
    proyecto_id: int
    codigo: str
    tipo: str
    descripcion: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
