from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class TipoDiagrama(str, Enum):
    CLASS = "class"
    SEQUENCE = "sequence"
    PACKAGE = "package"
    USECASE = "usecase"


class DiagramaElementoCreate(BaseModel):
    """Schema para crear elemento en diagrama"""
    id: str
    tipo: str
    nombre: str
    x: int
    y: int
    ancho: Optional[int] = None
    alto: Optional[int] = None
    color: Optional[str] = "#3b82f6"
    propiedades: Optional[Dict[str, Any]] = {}


class DiagramaConexionCreate(BaseModel):
    """Schema para crear conexión entre elementos"""
    id: str
    elemento_origen: str
    elemento_destino: str
    tipo: str
    etiqueta: Optional[str] = None
    puntos_control: Optional[List[Dict[str, int]]] = []


class VistaTransform(BaseModel):
    """Schema para la transformación de vista (pan, zoom)"""
    scale: float = 1.0
    translateX: float = 0
    translateY: float = 0


class DiagramaCreate(BaseModel):
    id_proyecto: int
    nombre: str = Field(..., min_length=1, max_length=255)
    tipo: TipoDiagrama
    descripcion: Optional[str] = None


class DiagramaUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    descripcion: Optional[str] = None
    elementos: Optional[List[DiagramaElementoCreate]] = None
    conexiones: Optional[List[DiagramaConexionCreate]] = None
    vista_actual: Optional[VistaTransform] = None


class DiagramaGuardarEstado(BaseModel):
    """Schema para guardar estado completo del diagrama"""
    elementos: List[DiagramaElementoCreate]
    conexiones: List[DiagramaConexionCreate]
    vista_actual: VistaTransform


class DiagramaResponse(BaseModel):
    id_diagrama: int
    id_proyecto: int
    nombre: str
    tipo: TipoDiagrama
    descripcion: Optional[str] = None
    elementos: List[DiagramaElementoCreate] = []
    conexiones: List[DiagramaConexionCreate] = []
    vista_actual: Optional[VistaTransform] = None
    id_usuario_creador: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DiagramaListResponse(BaseModel):
    total: int
    items: List[DiagramaResponse]
