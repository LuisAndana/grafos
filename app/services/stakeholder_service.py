# app/services/stakeholder_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.stakeholder import Stakeholder
from app.models.proyecto import Proyecto
from app.schemas.stakeholder_schema import StakeholderCreate, StakeholderUpdate


def _verificar_proyecto_del_usuario(db: Session, proyecto_id: int, user_id: int):
    proyecto = (
        db.query(Proyecto)
        .filter(Proyecto.id_proyecto == proyecto_id, Proyecto.user_id == user_id)
        .first()
    )
    if not proyecto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado o no pertenece al usuario.",
        )
    return proyecto


def create_stakeholder(db: Session, data: StakeholderCreate, user_id: int) -> Stakeholder:
    if data.proyecto_id:
        _verificar_proyecto_del_usuario(db, data.proyecto_id, user_id)

    stakeholder = Stakeholder(
        proyecto_id=data.proyecto_id,
        nombre=data.nombre,
        rol=data.rol,
        tipo=data.tipo,
        area=data.area,
        nivel_influencia=data.nivel_influencia,
        interes_sistema=data.interes_sistema,
    )
    db.add(stakeholder)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar stakeholder: {str(e)}",
        )

    # Re-leer desde la BD para obtener el objeto completo con id y timestamps
    db.refresh(stakeholder)
    return stakeholder


def get_stakeholders_by_proyecto(db: Session, proyecto_id: int, user_id: int) -> list[Stakeholder]:
    _verificar_proyecto_del_usuario(db, proyecto_id, user_id)
    return (
        db.query(Stakeholder)
        .filter(Stakeholder.proyecto_id == proyecto_id)
        .order_by(Stakeholder.created_at.desc())
        .all()
    )


def get_all_stakeholders_for_user(db: Session, user_id: int) -> list[Stakeholder]:
    proyecto_ids = (
        db.query(Proyecto.id_proyecto)
        .filter(Proyecto.user_id == user_id)
        .subquery()
    )
    return (
        db.query(Stakeholder)
        .filter(Stakeholder.proyecto_id.in_(proyecto_ids))
        .order_by(Stakeholder.created_at.desc())
        .all()
    )


def get_stakeholder(db: Session, stakeholder_id: int, user_id: int) -> Stakeholder:
    stakeholder = db.query(Stakeholder).filter(Stakeholder.id_stake == stakeholder_id).first()
    if not stakeholder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stakeholder no encontrado.",
        )
    if stakeholder.proyecto_id:
        _verificar_proyecto_del_usuario(db, stakeholder.proyecto_id, user_id)
    return stakeholder


def update_stakeholder(
    db: Session, stakeholder_id: int, data: StakeholderUpdate, user_id: int
) -> Stakeholder:
    stakeholder = get_stakeholder(db, stakeholder_id, user_id)
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(stakeholder, field, value)

    db.commit()
    db.refresh(stakeholder)
    return stakeholder


def delete_stakeholder(db: Session, stakeholder_id: int, user_id: int) -> dict:
    stakeholder = get_stakeholder(db, stakeholder_id, user_id)
    nombre = stakeholder.nombre
    db.delete(stakeholder)
    db.commit()
    return {"detail": f"Stakeholder '{nombre}' eliminado correctamente."}