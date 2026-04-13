from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.tipo_usuario_proyecto import TipoUsuarioProyecto
from app.models.proyecto import Proyecto
from app.schemas.tipo_usuario_schema import TipoUsuarioCreate, TipoUsuarioUpdate


def _verificar_proyecto(db: Session, proyecto_id: int):
    proyecto = db.query(Proyecto).filter(Proyecto.id_proyecto == proyecto_id).first()
    if not proyecto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado.",
        )
    return proyecto


def create_tipo_usuario(db: Session, data: TipoUsuarioCreate) -> TipoUsuarioProyecto:
    _verificar_proyecto(db, data.proyecto_id)

    registro = TipoUsuarioProyecto(
        proyecto_id=data.proyecto_id,
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
            detail=f"Error al guardar tipo de usuario: {str(e)}",
        )
    db.refresh(registro)
    return registro


def get_tipos_usuario_by_proyecto(db: Session, proyecto_id: int) -> list[TipoUsuarioProyecto]:
    _verificar_proyecto(db, proyecto_id)
    return (
        db.query(TipoUsuarioProyecto)
        .filter(TipoUsuarioProyecto.proyecto_id == proyecto_id)
        .order_by(TipoUsuarioProyecto.created_at.desc())
        .all()
    )


def get_tipo_usuario(db: Session, tipo_usuario_id: int) -> TipoUsuarioProyecto:
    registro = (
        db.query(TipoUsuarioProyecto)
        .filter(TipoUsuarioProyecto.id_tipo_usuario == tipo_usuario_id)
        .first()
    )
    if not registro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de usuario no encontrado.",
        )
    return registro


def update_tipo_usuario(
    db: Session, tipo_usuario_id: int, data: TipoUsuarioUpdate
) -> TipoUsuarioProyecto:
    registro = get_tipo_usuario(db, tipo_usuario_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(registro, field, value)
    db.commit()
    db.refresh(registro)
    return registro


def delete_tipo_usuario(db: Session, tipo_usuario_id: int) -> dict:
    registro = get_tipo_usuario(db, tipo_usuario_id)
    tipo = registro.tipo
    db.delete(registro)
    db.commit()
    return {"detail": f"Tipo de usuario '{tipo}' eliminado correctamente."}
