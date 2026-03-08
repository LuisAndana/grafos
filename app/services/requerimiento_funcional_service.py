# app/services/requerimiento_funcional_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.requerimiento_funcional import RequerimientoFuncional
from app.models.proyecto import Proyecto
from app.schemas.requerimiento_funcional_schema import (
    RequerimientoFuncionalCreate,
    RequerimientoFuncionalUpdate,
)


# ─── helpers ──────────────────────────────────────────────────────────────────

def _generar_codigo(db: Session, proyecto_id: int | None) -> str:
    """Genera el siguiente código RF-001, RF-002… por proyecto."""
    q = db.query(RequerimientoFuncional)
    if proyecto_id:
        q = q.filter(RequerimientoFuncional.proyecto_id == proyecto_id)
    total = q.count()
    return f"RF-{str(total + 1).zfill(3)}"


def _get_rf_or_404(db: Session, id_req: int, user_id: int) -> RequerimientoFuncional:
    rf = db.query(RequerimientoFuncional).filter(
        RequerimientoFuncional.id_req == id_req
    ).first()

    if not rf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Requerimiento no encontrado")

    # Verificar que el proyecto pertenece al usuario (si tiene proyecto)
    if rf.proyecto_id:
        proyecto = db.query(Proyecto).filter(
            Proyecto.id_proyecto == rf.proyecto_id,
            Proyecto.user_id == user_id,
        ).first()
        if not proyecto:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Sin acceso a este requerimiento")
    return rf


# ─── CRUD ─────────────────────────────────────────────────────────────────────

def create_rf(db: Session, data: RequerimientoFuncionalCreate, user_id: int) -> RequerimientoFuncional:
    # Verificar que el proyecto pertenece al usuario
    if data.proyecto_id:
        proyecto = db.query(Proyecto).filter(
            Proyecto.id_proyecto == data.proyecto_id,
            Proyecto.user_id == user_id,
        ).first()
        if not proyecto:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Proyecto no encontrado")

    codigo = _generar_codigo(db, data.proyecto_id)

    rf = RequerimientoFuncional(
        proyecto_id=data.proyecto_id,
        codigo=codigo,
        descripcion=data.descripcion,
        actor=data.actor,
        prioridad=data.prioridad,
        estado=data.estado,
    )
    db.add(rf)
    db.commit()
    db.refresh(rf)
    return rf


def get_rfs(db: Session, user_id: int, proyecto_id: int | None = None) -> list[RequerimientoFuncional]:
    q = db.query(RequerimientoFuncional)

    if proyecto_id:
        # Verificar pertenencia
        proyecto = db.query(Proyecto).filter(
            Proyecto.id_proyecto == proyecto_id,
            Proyecto.user_id == user_id,
        ).first()
        if not proyecto:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Proyecto no encontrado")
        q = q.filter(RequerimientoFuncional.proyecto_id == proyecto_id)
    else:
        # Devolver solo los RFs de proyectos del usuario
        ids_proyectos = db.query(Proyecto.id_proyecto).filter(
            Proyecto.user_id == user_id
        ).scalar_subquery()
        q = q.filter(RequerimientoFuncional.proyecto_id.in_(ids_proyectos))

    return q.order_by(RequerimientoFuncional.id_req).all()


def get_rf(db: Session, id_req: int, user_id: int) -> RequerimientoFuncional:
    return _get_rf_or_404(db, id_req, user_id)


def update_rf(
    db: Session,
    id_req: int,
    data: RequerimientoFuncionalUpdate,
    user_id: int,
) -> RequerimientoFuncional:
    rf = _get_rf_or_404(db, id_req, user_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(rf, field, value)
    db.commit()
    db.refresh(rf)
    return rf


def delete_rf(db: Session, id_req: int, user_id: int) -> dict:
    rf = _get_rf_or_404(db, id_req, user_id)
    db.delete(rf)
    db.commit()
    return {"message": f"Requerimiento {rf.codigo} eliminado"}