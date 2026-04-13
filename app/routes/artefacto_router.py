from fastapi import APIRouter, Depends, Form, Query, UploadFile, File, status
from fastapi.responses import FileResponse
from pathlib import Path
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.schemas.artefacto_schema import ArtefactoResponse
from app.services import artefacto_service as crud

router = APIRouter(prefix="/api/artefactos", tags=["Artefactos"])


@router.get("/", response_model=list[ArtefactoResponse])
def listar_artefactos(
    proyecto_id: Optional[int] = Query(None, description="Filtrar por proyecto"),
    db: Session = Depends(get_db),
):
    if proyecto_id:
        return crud.get_artefactos_by_proyecto(db, proyecto_id)
    return []


@router.post("/", response_model=ArtefactoResponse, status_code=status.HTTP_201_CREATED)
def subir_artefacto(
    proyecto_id: int = Form(...),
    nombre: str = Form(...),
    categoria: str = Form(...),
    descripcion: Optional[str] = Form(None),
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    return crud.create_artefacto(db, proyecto_id, nombre, categoria, descripcion, archivo)


@router.get("/{artefacto_id}/descargar")
def descargar_artefacto(
    artefacto_id: int,
    db: Session = Depends(get_db),
):
    artefacto = crud.get_artefacto(db, artefacto_id)
    ruta = Path(artefacto.ruta_archivo)
    if not ruta.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Archivo no encontrado en el servidor.")
    return FileResponse(
        path=str(ruta),
        media_type=artefacto.tipo_mime,
        filename=artefacto.nombre_archivo,
    )


@router.delete("/{artefacto_id}")
def eliminar_artefacto(
    artefacto_id: int,
    db: Session = Depends(get_db),
):
    return crud.delete_artefacto(db, artefacto_id)
