# app/routes/rf_router.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.rf_service import (
    create_rf,
    get_rfs_by_proyecto,
    get_rf_by_id,
    update_rf,
    delete_rf,
    get_rfs_resumen
)
from app.schemas.rf_schema import (
    RequerimientoFuncionalCreate,
    RequerimientoFuncionalUpdate,
    RequerimientoFuncionalResponse,
    RequerimientoFuncionalResumen
)

router = APIRouter(prefix="/api/requerimientos-funcionales", tags=["Requerimientos Funcionales"])


@router.post("/", response_model=RequerimientoFuncionalResponse)
def crear_rf(
    data: RequerimientoFuncionalCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Crear un nuevo requerimiento funcional"""
    return create_rf(db, data, user.id)


@router.get("/", response_model=list[RequerimientoFuncionalResponse])
def listar_rfs(
    proyecto_id: int = Query(..., description="ID del proyecto"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Listar todos los requerimientos funcionales de un proyecto"""
    return get_rfs_by_proyecto(db, proyecto_id, user.id)


@router.get("/resumen", response_model=RequerimientoFuncionalResumen)
def resumen_rfs(
    proyecto_id: int = Query(..., description="ID del proyecto"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Obtener resumen de requerimientos funcionales"""
    return get_rfs_resumen(db, proyecto_id, user.id)


@router.get("/{id_req}", response_model=RequerimientoFuncionalResponse)
def obtener_rf(
    id_req: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Obtener un requerimiento funcional específico"""
    rf = get_rf_by_id(db, id_req, user.id)
    if not rf:
        raise HTTPException(status_code=404, detail="Requerimiento funcional no encontrado")
    return rf


@router.put("/{id_req}", response_model=RequerimientoFuncionalResponse)
def actualizar_rf(
    id_req: int,
    data: RequerimientoFuncionalUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Actualizar un requerimiento funcional"""
    rf = get_rf_by_id(db, id_req, user.id)
    if not rf:
        raise HTTPException(status_code=404, detail="Requerimiento funcional no encontrado")
    return update_rf(db, rf, data)


@router.delete("/{id_req}")
def eliminar_rf(
    id_req: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Eliminar un requerimiento funcional"""
    rf = get_rf_by_id(db, id_req, user.id)
    if not rf:
        raise HTTPException(status_code=404, detail="Requerimiento funcional no encontrado")
    delete_rf(db, rf)
    return {"message": "Requerimiento funcional eliminado correctamente"}