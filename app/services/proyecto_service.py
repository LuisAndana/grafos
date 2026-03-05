from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.models.proyecto import Proyecto
from app.schemas.proyecto_schema import ProyectoCreate, ProyectoUpdate


# ─────────────────────────────────────────────
# CREATE
# ─────────────────────────────────────────────

def create_proyecto(db: Session, data: ProyectoCreate, user_id: int) -> Proyecto:
    """Crea un nuevo proyecto vinculado al usuario autenticado."""
    proyecto = Proyecto(
        user_id=user_id,
        nombre=data.nombre,
        codigo=data.codigo,
        descripcion_problema=data.descripcion_problema,
        objetivo_general=data.objetivo_general,
        fecha_inicio=data.fecha_inicio,
        analista_responsable=data.analista_responsable,
    )
    db.add(proyecto)
    try:
        db.commit()
        db.refresh(proyecto)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un proyecto con el código '{data.codigo}'.",
        )
    return proyecto


# ─────────────────────────────────────────────
# READ
# ─────────────────────────────────────────────

def get_proyectos(db: Session, user_id: int) -> list[Proyecto]:
    """Lista todos los proyectos del usuario."""
    return (
        db.query(Proyecto)
        .filter(Proyecto.user_id == user_id)
        .order_by(Proyecto.created_at.desc())
        .all()
    )


def get_proyecto(db: Session, proyecto_id: int, user_id: int) -> Proyecto:
    """Obtiene un proyecto por ID (solo si pertenece al usuario)."""
    proyecto = (
        db.query(Proyecto)
        .filter(Proyecto.id_proyecto == proyecto_id, Proyecto.user_id == user_id)
        .first()
    )
    if not proyecto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado.",
        )
    return proyecto


# ─────────────────────────────────────────────
# UPDATE
# ─────────────────────────────────────────────

def update_proyecto(
    db: Session, proyecto_id: int, data: ProyectoUpdate, user_id: int
) -> Proyecto:
    """Actualiza los campos enviados de un proyecto."""
    proyecto = get_proyecto(db, proyecto_id, user_id)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(proyecto, field, value)

    try:
        db.commit()
        db.refresh(proyecto)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El código de proyecto ya está en uso.",
        )
    return proyecto


# ─────────────────────────────────────────────
# DELETE
# ─────────────────────────────────────────────

def delete_proyecto(db: Session, proyecto_id: int, user_id: int) -> dict:
    """Elimina un proyecto (cascade en BD eliminará datos relacionados)."""
    proyecto = get_proyecto(db, proyecto_id, user_id)
    db.delete(proyecto)
    db.commit()
    return {"detail": f"Proyecto '{proyecto.nombre}' eliminado correctamente."}