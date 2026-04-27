from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.schemas.validacion_schema import ValidacionCreate, ValidacionUpdate, ValidacionResponse
from app.services import validacion_service as crud

router = APIRouter(prefix="/api/validacion", tags=["Validación"])


@router.get("/", response_model=Optional[ValidacionResponse])
def obtener_validacion(
    proyecto_id: int = Query(..., description="ID del proyecto"),
    db: Session = Depends(get_db),
):
    return crud.get_by_proyecto(db, proyecto_id)


@router.post("/", response_model=ValidacionResponse, status_code=status.HTTP_201_CREATED)
def crear_validacion(
    data: ValidacionCreate,
    db: Session = Depends(get_db),
):
    return crud.create_validacion(db, data)


@router.put("/{validacion_id}", response_model=ValidacionResponse)
def actualizar_validacion(
    validacion_id: int,
    data: ValidacionUpdate,
    db: Session = Depends(get_db),
):
    return crud.update_validacion(db, validacion_id, data)
