from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.caso_uso import CasoUso
from app.models.proyecto import Proyecto
from app.schemas.caso_uso_schema import CasoUsoCreate, CasoUsoUpdate


def _verificar_proyecto(db: Session, proyecto_id: int):
    proyecto = db.query(Proyecto).filter(Proyecto.id_proyecto == proyecto_id).first()
    if not proyecto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado.",
        )
    return proyecto


def create_caso_uso(db: Session, data: CasoUsoCreate) -> CasoUso:
    _verificar_proyecto(db, data.proyecto_id)

    registro = CasoUso(
        proyecto_id=data.proyecto_id,
        nombre=data.nombre,
        actores=data.actores or [],
        descripcion=data.descripcion,
        pasos=data.pasos or [],
    )
    db.add(registro)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar caso de uso: {str(e)}",
        )
    db.refresh(registro)
    return registro


def get_casos_uso_by_proyecto(db: Session, proyecto_id: int) -> list[CasoUso]:
    _verificar_proyecto(db, proyecto_id)
    return (
        db.query(CasoUso)
        .filter(CasoUso.proyecto_id == proyecto_id)
        .order_by(CasoUso.created_at.desc())
        .all()
    )


def get_caso_uso(db: Session, caso_uso_id: int) -> CasoUso:
    registro = db.query(CasoUso).filter(CasoUso.id_caso_uso == caso_uso_id).first()
    if not registro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Caso de uso no encontrado.",
        )
    return registro


def update_caso_uso(db: Session, caso_uso_id: int, data: CasoUsoUpdate) -> CasoUso:
    registro = get_caso_uso(db, caso_uso_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(registro, field, value)
    db.commit()
    db.refresh(registro)
    return registro


def delete_caso_uso(db: Session, caso_uso_id: int) -> dict:
    registro = get_caso_uso(db, caso_uso_id)
    nombre = registro.nombre
    db.delete(registro)
    db.commit()
    return {"detail": f"Caso de uso '{nombre}' eliminado correctamente."}
