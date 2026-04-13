from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.validacion import Validacion
from app.models.proyecto import Proyecto
from app.schemas.validacion_schema import ValidacionCreate, ValidacionUpdate


def _verificar_proyecto(db: Session, proyecto_id: int) -> Proyecto:
    proyecto = db.query(Proyecto).filter(Proyecto.id_proyecto == proyecto_id).first()
    if not proyecto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado.",
        )
    return proyecto


def get_by_proyecto(db: Session, proyecto_id: int) -> Validacion | None:
    return (
        db.query(Validacion)
        .filter(Validacion.proyecto_id == proyecto_id)
        .first()
    )


def get_by_id(db: Session, validacion_id: int) -> Validacion:
    registro = db.query(Validacion).filter(Validacion.id_validacion == validacion_id).first()
    if not registro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Validación no encontrada.",
        )
    return registro


def create_validacion(db: Session, data: ValidacionCreate) -> Validacion:
    _verificar_proyecto(db, data.proyecto_id)

    # Verificar que no exista ya una validación para este proyecto
    existente = get_by_proyecto(db, data.proyecto_id)
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una validación para este proyecto. Use PUT para actualizarla.",
        )

    registro = Validacion(
        proyecto_id=data.proyecto_id,
        checklist_rf=data.checklist_rf,
        checklist_rnf=data.checklist_rnf,
        checklist_casos_uso=data.checklist_casos_uso,
        checklist_restricciones=data.checklist_restricciones,
        checklist_prioridades=data.checklist_prioridades,
        observaciones=data.observaciones,
        aprobador=data.aprobador,
        fecha=data.fecha,
        firma_digital=data.firma_digital,
        aprobado=data.aprobado,
    )
    db.add(registro)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar validación: {str(e)}",
        )
    db.refresh(registro)
    return registro


def update_validacion(db: Session, validacion_id: int, data: ValidacionUpdate) -> Validacion:
    registro = get_by_id(db, validacion_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(registro, field, value)
    db.commit()
    db.refresh(registro)
    return registro
