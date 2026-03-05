# app/routes/stakeholder_router.py
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.stakeholder_schema import (
    StakeholderCreate,
    StakeholderUpdate,
    StakeholderResponse,
)
from app.services import stakeholder_service as crud

router = APIRouter(prefix="/stakeholders", tags=["Stakeholders"])


@router.post(
    "/",
    response_model=StakeholderResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_stakeholder(
    data: StakeholderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.create_stakeholder(db, data, user_id=current_user.id)


@router.get("/", response_model=list[StakeholderResponse])
def listar_stakeholders(
    proyecto_id: Optional[int] = Query(None, description="Filtrar por proyecto"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if proyecto_id:
        return crud.get_stakeholders_by_proyecto(db, proyecto_id, user_id=current_user.id)
    return crud.get_all_stakeholders_for_user(db, user_id=current_user.id)


@router.get("/{stakeholder_id}", response_model=StakeholderResponse)
def obtener_stakeholder(
    stakeholder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.get_stakeholder(db, stakeholder_id, user_id=current_user.id)


@router.put("/{stakeholder_id}", response_model=StakeholderResponse)
def actualizar_stakeholder(
    stakeholder_id: int,
    data: StakeholderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.update_stakeholder(db, stakeholder_id, data, user_id=current_user.id)


@router.delete("/{stakeholder_id}")
def eliminar_stakeholder(
    stakeholder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.delete_stakeholder(db, stakeholder_id, user_id=current_user.id)