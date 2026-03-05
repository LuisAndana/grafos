# app/routes/elicitacion_router.py
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.elicitacion_schema import (
    EntrevistaCreate, EntrevistaResponse,
    ProcesoCreate, ProcesoResponse,
    NecesidadCreate, NecesidadResponse,
    ElicitacionResumen,
)
from app.services import elicitacion_service as crud

router = APIRouter(prefix="/elicitacion", tags=["Elicitación"])


# ═══════════ RESUMEN ═══════════

@router.get("/resumen", response_model=ElicitacionResumen)
def resumen(
    proyecto_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return crud.get_resumen(db, user.id, proyecto_id)


# ═══════════ ENTREVISTAS ═══════════

@router.post("/entrevistas/", response_model=EntrevistaResponse, status_code=status.HTTP_201_CREATED)
def crear_entrevista(
    data: EntrevistaCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return crud.create_entrevista(db, data, user.id)


@router.get("/entrevistas/", response_model=list[EntrevistaResponse])
def listar_entrevistas(
    proyecto_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return crud.get_entrevistas(db, user.id, proyecto_id)


@router.delete("/entrevistas/{entrevista_id}")
def eliminar_entrevista(
    entrevista_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return crud.delete_entrevista(db, entrevista_id, user.id)


# ═══════════ PROCESOS ═══════════

@router.post("/procesos/", response_model=ProcesoResponse, status_code=status.HTTP_201_CREATED)
def crear_proceso(
    data: ProcesoCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return crud.create_proceso(db, data, user.id)


@router.get("/procesos/", response_model=list[ProcesoResponse])
def listar_procesos(
    proyecto_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return crud.get_procesos(db, user.id, proyecto_id)


@router.delete("/procesos/{proceso_id}")
def eliminar_proceso(
    proceso_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return crud.delete_proceso(db, proceso_id, user.id)


# ═══════════ NECESIDADES ═══════════

@router.post("/necesidades/", response_model=NecesidadResponse, status_code=status.HTTP_201_CREATED)
def crear_necesidad(
    data: NecesidadCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return crud.create_necesidad(db, data, user.id)


@router.get("/necesidades/", response_model=list[NecesidadResponse])
def listar_necesidades(
    proyecto_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return crud.get_necesidades(db, user.id, proyecto_id)


@router.delete("/necesidades/{necesidad_id}")
def eliminar_necesidad(
    necesidad_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return crud.delete_necesidad(db, necesidad_id, user.id)