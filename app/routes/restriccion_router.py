from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.schemas.restriccion_schema import RestriccionCreate, RestriccionUpdate, RestriccionResponse
from app.services import restriccion_service as crud

router = APIRouter(prefix="/api/restricciones", tags=["Restricciones"])


@router.get("/", response_model=list[RestriccionResponse])
def listar_restricciones(
    proyecto_id: Optional[int] = Query(None, description="Filtrar por proyecto"),
    db: Session = Depends(get_db),
):
    if proyecto_id:
        return crud.get_restricciones_by_proyecto(db, proyecto_id)
    return []


@router.post("/", response_model=RestriccionResponse, status_code=status.HTTP_201_CREATED)
def crear_restriccion(
    data: RestriccionCreate,
    db: Session = Depends(get_db),
):
    return crud.create_restriccion(db, data)


@router.put("/{restriccion_id}", response_model=RestriccionResponse)
def actualizar_restriccion(
    restriccion_id: int,
    data: RestriccionUpdate,
    db: Session = Depends(get_db),
):
    return crud.update_restriccion(db, restriccion_id, data)


@router.delete("/{restriccion_id}")
def eliminar_restriccion(
    restriccion_id: int,
    db: Session = Depends(get_db),
):
    return crud.delete_restriccion(db, restriccion_id)
