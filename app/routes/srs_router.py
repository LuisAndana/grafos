# app/routes/srs_router.py
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.srs_schema import SrsDocumentoCreate, SrsDocumentoUpdate, SrsDocumentoResponse
from app.services.srs_service import SrsService
from io import BytesIO

router = APIRouter(prefix="/api/srs", tags=["SRS Documentos"])


@router.post("/")
async def create_srs(
        srs_data: SrsDocumentoCreate,
        db: Session = Depends(get_db)
):
    """Crea un nuevo documento SRS"""
    try:
        srs = SrsService.create_srs(db, srs_data)
        return {
            "success": True,
            "data": {
                "id_srs": srs.id_srs,
                "proyecto_id": srs.proyecto_id,
                "nombre_documento": srs.nombre_documento,
                "estado": srs.estado,
                "version": srs.version,
                "created_at": srs.created_at
            },
            "message": "SRS creado exitosamente"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{srs_id}")
async def get_srs(
        srs_id: int,
        db: Session = Depends(get_db)
):
    """Obtiene un SRS por ID"""
    try:
        srs = SrsService.get_srs_by_id(db, srs_id)
        if not srs:
            raise HTTPException(status_code=404, detail="SRS no encontrado")

        return {
            "success": True,
            "data": {
                "id_srs": srs.id_srs,
                "proyecto_id": srs.proyecto_id,
                "nombre_documento": srs.nombre_documento,
                "introduccion": srs.introduccion,
                "stakeholders": srs.stakeholders,
                "usuarios": srs.usuarios,
                "requerimientos_funcionales": srs.requerimientos_funcionales,
                "requerimientos_no_funcionales": srs.requerimientos_no_funcionales,
                "casos_uso": srs.casos_uso,
                "restricciones": srs.restricciones,
                "estado": srs.estado,
                "version": srs.version,
                "created_at": srs.created_at,
                "updated_at": srs.updated_at
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proyecto/{proyecto_id}")
async def get_srs_by_proyecto(
        proyecto_id: int,
        db: Session = Depends(get_db)
):
    """Obtiene todos los SRS de un proyecto"""
    try:
        srs_list = SrsService.get_srs_by_proyecto(db, proyecto_id)

        return {
            "success": True,
            "data": [
                {
                    "id_srs": srs.id_srs,
                    "proyecto_id": srs.proyecto_id,
                    "nombre_documento": srs.nombre_documento,
                    "estado": srs.estado,
                    "version": srs.version,
                    "created_at": srs.created_at,
                    "updated_at": srs.updated_at
                }
                for srs in srs_list
            ],
            "count": len(srs_list)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{srs_id}")
async def update_srs(
        srs_id: int,
        srs_data: SrsDocumentoUpdate,
        db: Session = Depends(get_db)
):
    """Actualiza un SRS"""
    try:
        srs = SrsService.update_srs(db, srs_id, srs_data)
        if not srs:
            raise HTTPException(status_code=404, detail="SRS no encontrado")

        return {
            "success": True,
            "data": {
                "id_srs": srs.id_srs,
                "proyecto_id": srs.proyecto_id,
                "nombre_documento": srs.nombre_documento,
                "estado": srs.estado,
                "version": srs.version
            },
            "message": "SRS actualizado exitosamente"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{srs_id}")
async def delete_srs(
        srs_id: int,
        db: Session = Depends(get_db)
):
    """Elimina un SRS"""
    try:
        deleted = SrsService.delete_srs(db, srs_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="SRS no encontrado")

        return {
            "success": True,
            "message": "SRS eliminado exitosamente"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-generar/{proyecto_id}")
async def auto_generar_srs(
        proyecto_id: int,
        db: Session = Depends(get_db),
):
    """
    Genera (o actualiza) automáticamente un SRS completo
    a partir de TODOS los módulos del proyecto:
    Stakeholders, Elicitación, Requerimientos, RNF,
    Casos de Uso, Restricciones, Negociación, Validación y Artefactos.
    """
    try:
        srs = SrsService.auto_generar_srs(db, proyecto_id)
        if not srs:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")

        return {
            "success": True,
            "data": {
                "id_srs": srs.id_srs,
                "proyecto_id": srs.proyecto_id,
                "nombre_documento": srs.nombre_documento,
                "introduccion": srs.introduccion,
                "stakeholders": srs.stakeholders,
                "usuarios": srs.usuarios,
                "requerimientos_funcionales": srs.requerimientos_funcionales,
                "requerimientos_no_funcionales": srs.requerimientos_no_funcionales,
                "casos_uso": srs.casos_uso,
                "restricciones": srs.restricciones,
                "elicitacion": srs.elicitacion,
                "negociaciones": srs.negociaciones,
                "validacion_info": srs.validacion_info,
                "artefactos_info": srs.artefactos_info,
                "estado": srs.estado,
                "version": srs.version,
                "created_at": srs.created_at,
                "updated_at": srs.updated_at,
            },
            "message": "SRS auto-generado exitosamente desde todos los módulos del proyecto",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/generar-pdf/{srs_id}")
async def generate_srs_pdf(
        srs_id: int,
        proyecto_id: int = Query(...),
        db: Session = Depends(get_db)
):
    """Genera un PDF del documento SRS"""
    try:
        pdf_buffer = SrsService.generate_pdf(db, srs_id, proyecto_id)
        if not pdf_buffer:
            raise HTTPException(status_code=404, detail="SRS no encontrado")

        return StreamingResponse(
            iter([pdf_buffer.getvalue()]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=SRS_{srs_id}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))