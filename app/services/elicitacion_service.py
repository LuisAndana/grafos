# app/services/elicitacion_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.proyecto import Proyecto
from app.models.elicitacion import (
    ElicitacionEntrevista,
    ElicitacionProceso,
    ElicitacionNecesidad,
)
from app.schemas.elicitacion_schema import (
    EntrevistaCreate,
    ProcesoCreate,
    NecesidadCreate,
)


def _verificar_proyecto(db: Session, proyecto_id: int, user_id: int):
    proyecto = (
        db.query(Proyecto)
        .filter(Proyecto.id_proyecto == proyecto_id, Proyecto.user_id == user_id)
        .first()
    )
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado.")
    return proyecto


def _get_proyecto_ids(db: Session, user_id: int):
    return (
        db.query(Proyecto.id_proyecto)
        .filter(Proyecto.user_id == user_id)
        .subquery()
    )


# ═══════════════════════════════════════════════
# ENTREVISTAS
# ═══════════════════════════════════════════════

def create_entrevista(db: Session, data: EntrevistaCreate, user_id: int):
    if data.proyecto_id:
        _verificar_proyecto(db, data.proyecto_id, user_id)

    obj = ElicitacionEntrevista(
        proyecto_id=data.proyecto_id,
        pregunta=data.pregunta,
        respuesta=data.respuesta,
        observaciones=data.observaciones,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_entrevistas(db: Session, user_id: int, proyecto_id: int = None):
    if proyecto_id:
        _verificar_proyecto(db, proyecto_id, user_id)
        return db.query(ElicitacionEntrevista).filter(
            ElicitacionEntrevista.proyecto_id == proyecto_id
        ).order_by(ElicitacionEntrevista.created_at.desc()).all()

    ids = _get_proyecto_ids(db, user_id)
    return db.query(ElicitacionEntrevista).filter(
        ElicitacionEntrevista.proyecto_id.in_(ids)
    ).order_by(ElicitacionEntrevista.created_at.desc()).all()


def delete_entrevista(db: Session, entrevista_id: int, user_id: int):
    obj = db.query(ElicitacionEntrevista).filter(
        ElicitacionEntrevista.id_entrevista == entrevista_id
    ).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Entrevista no encontrada.")
    if obj.proyecto_id:
        _verificar_proyecto(db, obj.proyecto_id, user_id)
    db.delete(obj)
    db.commit()
    return {"detail": "Entrevista eliminada."}


# ═══════════════════════════════════════════════
# PROCESOS
# ═══════════════════════════════════════════════

def create_proceso(db: Session, data: ProcesoCreate, user_id: int):
    if data.proyecto_id:
        _verificar_proyecto(db, data.proyecto_id, user_id)

    obj = ElicitacionProceso(
        proyecto_id=data.proyecto_id,
        nombre_proceso=data.nombre_proceso,
        descripcion=data.descripcion,
        problemas_detectados=data.problemas_detectados,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_procesos(db: Session, user_id: int, proyecto_id: int = None):
    if proyecto_id:
        _verificar_proyecto(db, proyecto_id, user_id)
        return db.query(ElicitacionProceso).filter(
            ElicitacionProceso.proyecto_id == proyecto_id
        ).order_by(ElicitacionProceso.created_at.desc()).all()

    ids = _get_proyecto_ids(db, user_id)
    return db.query(ElicitacionProceso).filter(
        ElicitacionProceso.proyecto_id.in_(ids)
    ).order_by(ElicitacionProceso.created_at.desc()).all()


def delete_proceso(db: Session, proceso_id: int, user_id: int):
    obj = db.query(ElicitacionProceso).filter(
        ElicitacionProceso.id_proceso == proceso_id
    ).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Proceso no encontrado.")
    if obj.proyecto_id:
        _verificar_proyecto(db, obj.proyecto_id, user_id)
    db.delete(obj)
    db.commit()
    return {"detail": "Proceso eliminado."}


# ═══════════════════════════════════════════════
# NECESIDADES
# ═══════════════════════════════════════════════

def create_necesidad(db: Session, data: NecesidadCreate, user_id: int):
    if data.proyecto_id:
        _verificar_proyecto(db, data.proyecto_id, user_id)

    obj = ElicitacionNecesidad(
        proyecto_id=data.proyecto_id,
        nombre=data.nombre,
        es_predefinida=data.es_predefinida,
        seleccionada=data.seleccionada,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_necesidades(db: Session, user_id: int, proyecto_id: int = None):
    if proyecto_id:
        _verificar_proyecto(db, proyecto_id, user_id)
        return db.query(ElicitacionNecesidad).filter(
            ElicitacionNecesidad.proyecto_id == proyecto_id
        ).order_by(ElicitacionNecesidad.created_at.desc()).all()

    ids = _get_proyecto_ids(db, user_id)
    return db.query(ElicitacionNecesidad).filter(
        ElicitacionNecesidad.proyecto_id.in_(ids)
    ).order_by(ElicitacionNecesidad.created_at.desc()).all()


def delete_necesidad(db: Session, necesidad_id: int, user_id: int):
    obj = db.query(ElicitacionNecesidad).filter(
        ElicitacionNecesidad.id_necesidad == necesidad_id
    ).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Necesidad no encontrada.")
    if obj.proyecto_id:
        _verificar_proyecto(db, obj.proyecto_id, user_id)
    db.delete(obj)
    db.commit()
    return {"detail": "Necesidad eliminada."}


# ═══════════════════════════════════════════════
# RESUMEN
# ═══════════════════════════════════════════════

def get_resumen(db: Session, user_id: int, proyecto_id: int = None):
    entrevistas = get_entrevistas(db, user_id, proyecto_id)
    procesos = get_procesos(db, user_id, proyecto_id)
    necesidades = get_necesidades(db, user_id, proyecto_id)
    return {
        "total_entrevistas": len(entrevistas),
        "total_procesos": len(procesos),
        "total_necesidades": len(necesidades),
    }