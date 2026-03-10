# app/routes/negociacion_router.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.negociacion_schema import (
    NegociacionCreate,
    NegociacionUpdate,
    NegociacionResponse,
)
from app.services.negociacion_service import NegociacionService

router = APIRouter(prefix="/api/negociacion", tags=["Negociación"])


@router.get("/")
async def get_negociaciones(
    proyecto_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """Obtiene todas las negociaciones de un proyecto"""
    try:
        negociaciones = NegociacionService.get_negociaciones_by_proyecto(db, proyecto_id)
        return {
            "success": True,
            "data": negociaciones,
            "count": len(negociaciones) if negociaciones else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{negociacion_id}")
async def get_negociacion(
    negociacion_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene una negociación específica"""
    try:
        negociacion = NegociacionService.get_negociacion_by_id(db, negociacion_id)
        if not negociacion:
            raise HTTPException(status_code=404, detail="Negociación no encontrada")
        return {
            "success": True,
            "data": negociacion
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_negociacion(
    negociacion: NegociacionCreate,
    db: Session = Depends(get_db)
):
    """Crea una nueva negociación"""
    try:
        new_negociacion = NegociacionService.create_negociacion(db, negociacion)
        return {
            "success": True,
            "data": new_negociacion,
            "message": "Negociación creada exitosamente"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{negociacion_id}")
async def update_negociacion(
    negociacion_id: int,
    negociacion: NegociacionUpdate,
    db: Session = Depends(get_db)
):
    """Actualiza una negociación"""
    try:
        updated = NegociacionService.update_negociacion(db, negociacion_id, negociacion)
        if not updated:
            raise HTTPException(status_code=404, detail="Negociación no encontrada")
        return {
            "success": True,
            "data": updated,
            "message": "Negociación actualizada exitosamente"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{negociacion_id}")
async def patch_negociacion(
    negociacion_id: int,
    negociacion: NegociacionUpdate,
    db: Session = Depends(get_db)
):
    """Actualiza parcialmente una negociación"""
    try:
        updated = NegociacionService.update_negociacion(db, negociacion_id, negociacion)
        if not updated:
            raise HTTPException(status_code=404, detail="Negociación no encontrada")
        return {
            "success": True,
            "data": updated,
            "message": "Negociación actualizada exitosamente"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{negociacion_id}")
async def delete_negociacion(
    negociacion_id: int,
    db: Session = Depends(get_db)
):
    """Elimina una negociación"""
    try:
        deleted = NegociacionService.delete_negociacion(db, negociacion_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Negociación no encontrada")
        return {
            "success": True,
            "message": "Negociación eliminada exitosamente"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resumen/{proyecto_id}")
async def get_resumen(
    proyecto_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene un resumen de negociaciones"""
    try:
        resumen = NegociacionService.get_negociaciones_resumen(db, proyecto_id)
        return {
            "success": True,
            "data": resumen
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))