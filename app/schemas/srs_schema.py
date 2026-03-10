# app/schemas/srs_schema.py
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class StakeholderSchema(BaseModel):
    name: str
    role: str
    responsibility: str


class UsuarioSchema(BaseModel):
    userId: str
    userType: str
    description: str


class RequerimientoFuncionalSchema(BaseModel):
    rfId: str
    description: str
    priority: str


class RequerimientoNoFuncionalSchema(BaseModel):
    rnfId: str
    category: str
    description: str


class CasoUsoSchema(BaseModel):
    useCase: str
    actors: List[str]
    description: str
    steps: List[str]


class RestriccionSchema(BaseModel):
    constraintId: str
    type: str
    description: str


class SrsDocumentoCreate(BaseModel):
    proyecto_id: int
    nombre_documento: str
    introduccion: Optional[str] = None
    stakeholders: Optional[List[StakeholderSchema]] = None
    usuarios: Optional[List[UsuarioSchema]] = None
    requerimientos_funcionales: Optional[List[RequerimientoFuncionalSchema]] = None
    requerimientos_no_funcionales: Optional[List[RequerimientoNoFuncionalSchema]] = None
    casos_uso: Optional[List[CasoUsoSchema]] = None
    restricciones: Optional[List[RestriccionSchema]] = None


class SrsDocumentoUpdate(BaseModel):
    nombre_documento: Optional[str] = None
    introduccion: Optional[str] = None
    stakeholders: Optional[List[StakeholderSchema]] = None
    usuarios: Optional[List[UsuarioSchema]] = None
    requerimientos_funcionales: Optional[List[RequerimientoFuncionalSchema]] = None
    requerimientos_no_funcionales: Optional[List[RequerimientoNoFuncionalSchema]] = None
    casos_uso: Optional[List[CasoUsoSchema]] = None
    restricciones: Optional[List[RestriccionSchema]] = None
    estado: Optional[str] = None
    version: Optional[str] = None


class SrsDocumentoResponse(BaseModel):
    id_srs: int
    proyecto_id: int
    nombre_documento: str
    introduccion: Optional[str]
    stakeholders: Optional[List[dict]]
    usuarios: Optional[List[dict]]
    requerimientos_funcionales: Optional[List[dict]]
    requerimientos_no_funcionales: Optional[List[dict]]
    casos_uso: Optional[List[dict]]
    restricciones: Optional[List[dict]]
    estado: str
    version: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True