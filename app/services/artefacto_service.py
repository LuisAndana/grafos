import os
import shutil
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.models.artefacto import Artefacto
from app.models.proyecto import Proyecto

# Directorio base donde se guardan los archivos
UPLOAD_DIR = Path("uploads/artefactos")


def _verificar_proyecto(db: Session, proyecto_id: int) -> Proyecto:
    proyecto = db.query(Proyecto).filter(Proyecto.id_proyecto == proyecto_id).first()
    if not proyecto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado.",
        )
    return proyecto


def get_artefactos_by_proyecto(db: Session, proyecto_id: int) -> list[Artefacto]:
    _verificar_proyecto(db, proyecto_id)
    return (
        db.query(Artefacto)
        .filter(Artefacto.proyecto_id == proyecto_id)
        .order_by(Artefacto.created_at.desc())
        .all()
    )


def get_artefacto(db: Session, artefacto_id: int) -> Artefacto:
    artefacto = db.query(Artefacto).filter(Artefacto.id_artefacto == artefacto_id).first()
    if not artefacto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artefacto no encontrado.",
        )
    return artefacto


def create_artefacto(
    db: Session,
    proyecto_id: int,
    nombre: str,
    categoria: str,
    descripcion: str | None,
    archivo: UploadFile,
) -> Artefacto:
    _verificar_proyecto(db, proyecto_id)

    # Crear directorio del proyecto si no existe
    directorio = UPLOAD_DIR / str(proyecto_id)
    directorio.mkdir(parents=True, exist_ok=True)

    # Evitar colisiones con nombre único
    nombre_original = archivo.filename or "archivo"
    nombre_seguro = _nombre_unico(directorio, nombre_original)
    ruta = directorio / nombre_seguro

    # Guardar archivo en disco y medir tamaño
    try:
        with open(ruta, "wb") as f:
            shutil.copyfileobj(archivo.file, f)
        tamanio = ruta.stat().st_size
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar el archivo: {str(e)}",
        )

    artefacto = Artefacto(
        proyecto_id=proyecto_id,
        nombre=nombre,
        categoria=categoria,
        descripcion=descripcion,
        nombre_archivo=nombre_original,
        ruta_archivo=str(ruta).replace("\\", "/"),
        tipo_mime=archivo.content_type or "application/octet-stream",
        tamanio=tamanio,
    )
    db.add(artefacto)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        ruta.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar artefacto: {str(e)}",
        )
    db.refresh(artefacto)
    return artefacto


def delete_artefacto(db: Session, artefacto_id: int) -> dict:
    artefacto = get_artefacto(db, artefacto_id)
    ruta = Path(artefacto.ruta_archivo)

    db.delete(artefacto)
    db.commit()

    # Eliminar archivo del disco (no falla si ya no existe)
    ruta.unlink(missing_ok=True)

    return {"detail": f"Artefacto '{artefacto.nombre}' eliminado correctamente."}


# ── helpers ──────────────────────────────────────────────────────────────────

def _nombre_unico(directorio: Path, nombre: str) -> str:
    """Agrega sufijo numérico si el archivo ya existe."""
    ruta = directorio / nombre
    if not ruta.exists():
        return nombre
    stem = Path(nombre).stem
    suffix = Path(nombre).suffix
    contador = 1
    while (directorio / f"{stem}_{contador}{suffix}").exists():
        contador += 1
    return f"{stem}_{contador}{suffix}"
