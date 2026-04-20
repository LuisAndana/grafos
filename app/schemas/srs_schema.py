# app/schemas/srs_schema.py
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


# ── Sub-schemas existentes ───────────────────────────────────────────────────

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


# ── Nuevos sub-schemas para datos de los módulos adicionales ─────────────────

class EntrevistaSchema(BaseModel):
    pregunta: str
    respuesta: Optional[str] = None
    observaciones: Optional[str] = None


class ProcesoSchema(BaseModel):
    nombre_proceso: str
    descripcion: Optional[str] = None
    problemas_detectados: Optional[str] = None


class NecesidadSchema(BaseModel):
    nombre: str


class ElicitacionSchema(BaseModel):
    entrevistas: Optional[List[EntrevistaSchema]] = None
    procesos: Optional[List[ProcesoSchema]] = None
    necesidades: Optional[List[NecesidadSchema]] = None


class NegociacionItemSchema(BaseModel):
    nombre: str
    descripcion: str
    prioridad: str
    aceptado: bool


class ValidacionInfoSchema(BaseModel):
    aprobado: Optional[bool] = None
    aprobador: Optional[str] = None
    observaciones: Optional[str] = None
    checklist_rf: Optional[bool] = None
    checklist_rnf: Optional[bool] = None
    checklist_casos_uso: Optional[bool] = None
    checklist_restricciones: Optional[bool] = None
    checklist_prioridades: Optional[bool] = None


class ArtefactoInfoSchema(BaseModel):
    nombre: str
    categoria: str
    descripcion: Optional[str] = None
    nombre_archivo: str
    tipo_mime: str


# ── Schemas CRUD del documento SRS ───────────────────────────────────────────

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
    elicitacion: Optional[ElicitacionSchema] = None
    negociaciones: Optional[List[NegociacionItemSchema]] = None
    validacion_info: Optional[ValidacionInfoSchema] = None
    artefactos_info: Optional[List[ArtefactoInfoSchema]] = None


class SrsDocumentoUpdate(BaseModel):
    nombre_documento: Optional[str] = None
    introduccion: Optional[str] = None
    stakeholders: Optional[List[StakeholderSchema]] = None
    usuarios: Optional[List[UsuarioSchema]] = None
    requerimientos_funcionales: Optional[List[RequerimientoFuncionalSchema]] = None
    requerimientos_no_funcionales: Optional[List[RequerimientoNoFuncionalSchema]] = None
    casos_uso: Optional[List[CasoUsoSchema]] = None
    restricciones: Optional[List[RestriccionSchema]] = None
    elicitacion: Optional[ElicitacionSchema] = None
    negociaciones: Optional[List[NegociacionItemSchema]] = None
    validacion_info: Optional[ValidacionInfoSchema] = None
    artefactos_info: Optional[List[ArtefactoInfoSchema]] = None
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
    elicitacion: Optional[dict] = None
    negociaciones: Optional[List[dict]] = None
    validacion_info: Optional[dict] = None
    artefactos_info: Optional[List[dict]] = None
    estado: str
    version: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
