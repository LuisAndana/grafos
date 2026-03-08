# app/routes/requerimiento_funcional_router.py
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.requerimiento_funcional_schema import (
    RequerimientoFuncionalCreate,
    RequerimientoFuncionalUpdate,
    RequerimientoFuncionalResponse,
)
from app.services import requerimiento_funcional_service as crud

router = APIRouter(prefix="/requerimientos-funcionales", tags=["Requerimientos Funcionales"])


@router.post(
    "/",
    response_model=RequerimientoFuncionalResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_rf(
    data: RequerimientoFuncionalCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return crud.create_rf(db, data, user.id)


@router.get("/", response_model=list[RequerimientoFuncionalResponse])
def listar_rfs(
    proyecto_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return crud.get_rfs(db, user.id, proyecto_id)


@router.get("/{id_req}", response_model=RequerimientoFuncionalResponse)
def obtener_rf(
    id_req: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return crud.get_rf(db, id_req, user.id)


@router.put("/{id_req}", response_model=RequerimientoFuncionalResponse)
def actualizar_rf(
    id_req: int,
    data: RequerimientoFuncionalUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return crud.update_rf(db, id_req, data, user.id)


@router.delete("/{id_req}")
def eliminar_rf(
    id_req: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return crud.delete_rf(db, id_req, user.id)