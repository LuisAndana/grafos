from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.schemas.caso_uso_schema import CasoUsoCreate, CasoUsoUpdate, CasoUsoResponse
from app.services import caso_uso_service as crud

router = APIRouter(prefix="/api/casos-uso", tags=["Casos de Uso"])


@router.get("/", response_model=list[CasoUsoResponse])
def listar_casos_uso(
    proyecto_id: Optional[int] = Query(None, description="Filtrar por proyecto"),
    db: Session = Depends(get_db),
):
    if proyecto_id:
        return crud.get_casos_uso_by_proyecto(db, proyecto_id)
    return []


@router.post("/", response_model=CasoUsoResponse, status_code=status.HTTP_201_CREATED)
def crear_caso_uso(
    data: CasoUsoCreate,
    db: Session = Depends(get_db),
):
    return crud.create_caso_uso(db, data)


@router.put("/{caso_uso_id}", response_model=CasoUsoResponse)
def actualizar_caso_uso(
    caso_uso_id: int,
    data: CasoUsoUpdate,
    db: Session = Depends(get_db),
):
    return crud.update_caso_uso(db, caso_uso_id, data)


@router.delete("/{caso_uso_id}")
def eliminar_caso_uso(
    caso_uso_id: int,
    db: Session = Depends(get_db),
):
    return crud.delete_caso_uso(db, caso_uso_id)
