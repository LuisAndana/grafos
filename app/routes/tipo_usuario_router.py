from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.schemas.tipo_usuario_schema import TipoUsuarioCreate, TipoUsuarioUpdate, TipoUsuarioResponse
from app.services import tipo_usuario_service as crud

router = APIRouter(prefix="/tipo-usuario", tags=["Tipo Usuario"])


@router.get("/", response_model=list[TipoUsuarioResponse])
def listar_tipos_usuario(
    proyecto_id: Optional[int] = Query(None, description="Filtrar por proyecto"),
    db: Session = Depends(get_db),
):
    if proyecto_id:
        return crud.get_tipos_usuario_by_proyecto(db, proyecto_id)
    return []


@router.post("/", response_model=TipoUsuarioResponse, status_code=status.HTTP_201_CREATED)
def crear_tipo_usuario(
    data: TipoUsuarioCreate,
    db: Session = Depends(get_db),
):
    return crud.create_tipo_usuario(db, data)


@router.put("/{tipo_usuario_id}", response_model=TipoUsuarioResponse)
def actualizar_tipo_usuario(
    tipo_usuario_id: int,
    data: TipoUsuarioUpdate,
    db: Session = Depends(get_db),
):
    return crud.update_tipo_usuario(db, tipo_usuario_id, data)


@router.delete("/{tipo_usuario_id}")
def eliminar_tipo_usuario(
    tipo_usuario_id: int,
    db: Session = Depends(get_db),
):
    return crud.delete_tipo_usuario(db, tipo_usuario_id)
