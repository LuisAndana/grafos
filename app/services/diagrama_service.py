from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.diagrama import Diagrama, TipoDiagrama
from app.models.proyecto import Proyecto
from app.schemas.diagrama_schema import (
    DiagramaCreate, DiagramaUpdate, DiagramaGuardarEstado
)


def _verificar_proyecto(db: Session, proyecto_id: int):
    """Verificar que el proyecto existe"""
    proyecto = db.query(Proyecto).filter(Proyecto.id_proyecto == proyecto_id).first()
    if not proyecto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado.",
        )
    return proyecto


def create_diagrama(db: Session, data: DiagramaCreate) -> Diagrama:
    """Crear nuevo diagrama"""
    _verificar_proyecto(db, data.id_proyecto)

    registro = Diagrama(
        id_proyecto=data.id_proyecto,
        nombre=data.nombre,
        tipo=data.tipo,
        descripcion=data.descripcion,
        elementos=[],
        conexiones=[],
        vista_actual={"scale": 1.0, "translateX": 0, "translateY": 0},
        id_usuario_creador=1,  # Este valor debería venir del token
    )
    db.add(registro)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar diagrama: {str(e)}",
        )
    db.refresh(registro)
    return registro


def get_diagramas_by_proyecto(db: Session, proyecto_id: int) -> list[Diagrama]:
    """Obtener todos los diagramas de un proyecto"""
    _verificar_proyecto(db, proyecto_id)
    return (
        db.query(Diagrama)
        .filter(Diagrama.id_proyecto == proyecto_id)
        .order_by(Diagrama.created_at.desc())
        .all()
    )


def get_diagramas_by_tipo(db: Session, proyecto_id: int, tipo: str) -> list[Diagrama]:
    """Obtener diagramas por tipo"""
    _verificar_proyecto(db, proyecto_id)
    try:
        tipo_enum = TipoDiagrama(tipo)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de diagrama inválido: {tipo}",
        )

    return (
        db.query(Diagrama)
        .filter(
            Diagrama.id_proyecto == proyecto_id,
            Diagrama.tipo == tipo_enum
        )
        .order_by(Diagrama.created_at.desc())
        .all()
    )


def get_diagrama(db: Session, diagrama_id: int) -> Diagrama:
    """Obtener un diagrama específico"""
    registro = db.query(Diagrama).filter(Diagrama.id_diagrama == diagrama_id).first()
    if not registro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagrama no encontrado.",
        )
    return registro


def update_diagrama(db: Session, diagrama_id: int, data: DiagramaUpdate) -> Diagrama:
    """Actualizar diagrama"""
    registro = get_diagrama(db, diagrama_id)
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field == "elementos" and value:
            registro.elementos = [elem.model_dump() for elem in value]
        elif field == "conexiones" and value:
            registro.conexiones = [conn.model_dump() for conn in value]
        elif field == "vista_actual" and value:
            registro.vista_actual = value.model_dump() if hasattr(value, 'model_dump') else value
        else:
            setattr(registro, field, value)

    db.commit()
    db.refresh(registro)
    return registro


def guardar_estado_diagrama(
    db: Session, diagrama_id: int, data: DiagramaGuardarEstado
) -> Diagrama:
    """Guardar estado completo del diagrama"""
    registro = get_diagrama(db, diagrama_id)

    registro.elementos = [elem.model_dump() for elem in data.elementos]
    registro.conexiones = [conn.model_dump() for conn in data.conexiones]
    registro.vista_actual = data.vista_actual.model_dump() if hasattr(
        data.vista_actual, 'model_dump'
    ) else data.vista_actual

    db.commit()
    db.refresh(registro)
    return registro


def delete_diagrama(db: Session, diagrama_id: int) -> dict:
    """Eliminar diagrama"""
    registro = get_diagrama(db, diagrama_id)
    nombre = registro.nombre
    db.delete(registro)
    db.commit()
    return {"detail": f"Diagrama '{nombre}' eliminado correctamente."}


def contar_diagramas_proyecto(db: Session, proyecto_id: int) -> int:
    """Contar diagramas en un proyecto"""
    _verificar_proyecto(db, proyecto_id)
    return db.query(Diagrama).filter(Diagrama.id_proyecto == proyecto_id).count()
