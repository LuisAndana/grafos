# app/routes/rnf_router.py
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.rnf_schema import RNFCreate, RNFUpdate, RNFResponse, RNFResumen
from app.services import rnf_service as crud

router = APIRouter(prefix="/rnf", tags=["Requerimientos No Funcionales"])


# ═══════════ RESUMEN ═══════════

@router.get("/resumen", response_model=RNFResumen)
def resumen(
    proyecto_id: int = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return crud.get_resumen_rnf(db, proyecto_id, user.id)


# ═══════════ CREAR ═══════════

@router.post("/", response_model=RNFResponse, status_code=status.HTTP_201_CREATED)
def crear_rnf(
    data: RNFCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return crud.create_rnf(db, data, user.id)


# ═══════════ LISTAR ═══════════

@router.get("/", response_model=list[RNFResponse])
def listar_rnfs(
    proyecto_id: int = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return crud.get_rnfs_by_proyecto(db, proyecto_id, user.id)


# ═══════════ OBTENER UNO ═══════════

@router.get("/{rnf_id}", response_model=RNFResponse)
def obtener_rnf(
    rnf_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return crud.get_rnf(db, rnf_id, user.id)


# ═══════════ ACTUALIZAR ═══════════

@router.put("/{rnf_id}", response_model=RNFResponse)
def actualizar_rnf(
    rnf_id: int,
    data: RNFUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return crud.update_rnf(db, rnf_id, data, user.id)


# ═══════════ ELIMINAR ═══════════

@router.delete("/{rnf_id}")
def eliminar_rnf(
    rnf_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return crud.delete_rnf(db, rnf_id, user.id)