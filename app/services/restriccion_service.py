from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.restriccion import Restriccion
from app.models.proyecto import Proyecto
from app.schemas.restriccion_schema import RestriccionCreate, RestriccionUpdate


def _verificar_proyecto(db: Session, proyecto_id: int):
    proyecto = db.query(Proyecto).filter(Proyecto.id_proyecto == proyecto_id).first()
    if not proyecto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado.",
        )
    return proyecto


def create_restriccion(db: Session, data: RestriccionCreate) -> Restriccion:
    _verificar_proyecto(db, data.proyecto_id)

    registro = Restriccion(
        proyecto_id=data.proyecto_id,
        codigo=data.codigo,
        tipo=data.tipo,
        descripcion=data.descripcion,
    )
    db.add(registro)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar restricción: {str(e)}",
        )
    db.refresh(registro)
    return registro


def get_restricciones_by_proyecto(db: Session, proyecto_id: int) -> list[Restriccion]:
    _verificar_proyecto(db, proyecto_id)
    return (
        db.query(Restriccion)
        .filter(Restriccion.proyecto_id == proyecto_id)
        .order_by(Restriccion.created_at.desc())
        .all()
    )


def get_restriccion(db: Session, restriccion_id: int) -> Restriccion:
    registro = db.query(Restriccion).filter(Restriccion.id_restriccion == restriccion_id).first()
    if not registro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restricción no encontrada.",
        )
    return registro


def update_restriccion(db: Session, restriccion_id: int, data: RestriccionUpdate) -> Restriccion:
    registro = get_restriccion(db, restriccion_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(registro, field, value)
    db.commit()
    db.refresh(registro)
    return registro


def delete_restriccion(db: Session, restriccion_id: int) -> dict:
    registro = get_restriccion(db, restriccion_id)
    codigo = registro.codigo
    db.delete(registro)
    db.commit()
    return {"detail": f"Restricción '{codigo}' eliminada correctamente."}
