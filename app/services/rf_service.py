# app/services/rf_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.requerimiento_funcional import RequerimientoFuncional
from app.schemas.rf_schema import (
    RequerimientoFuncionalCreate,
    RequerimientoFuncionalUpdate,
    RequerimientoFuncionalResumen
)


def _generar_codigo(db: Session, proyecto_id: int) -> str:
    """
    Genera el código del siguiente requerimiento funcional
    Ej: RF-001, RF-002, etc.
    """
    ultimo = (
        db.query(RequerimientoFuncional)
        .filter(RequerimientoFuncional.proyecto_id == proyecto_id)
        .order_by(RequerimientoFuncional.id_req.desc())
        .first()
    )

    if not ultimo or not ultimo.codigo:
        return "RF-001"

    # Extraer número del código (ej: "RF-001" → 1)
    try:
        numero = int(ultimo.codigo.split("-")[1])
        return f"RF-{numero + 1:03d}"
    except (IndexError, ValueError):
        return "RF-001"


def create_rf(db: Session, data: RequerimientoFuncionalCreate, user_id: int) -> RequerimientoFuncional:
    """Crear un nuevo requerimiento funcional"""
    codigo = _generar_codigo(db, data.proyecto_id)

    rf = RequerimientoFuncional(
        proyecto_id=data.proyecto_id,
        codigo=codigo,
        descripcion=data.descripcion,
        actor=data.actor,
        prioridad=data.prioridad,  # Ahora es string, se guarda tal cual
        estado=data.estado  # Ahora es string, se guarda tal cual
    )

    db.add(rf)
    db.commit()
    db.refresh(rf)
    return rf


def get_rfs_by_proyecto(db: Session, proyecto_id: int, user_id: int) -> list[RequerimientoFuncional]:
    """Obtener todos los RFs de un proyecto (verificando que pertenezca al usuario)"""
    # Verificar que el proyecto pertenezca al usuario
    from app.models.proyecto import Proyecto
    proyecto = db.query(Proyecto).filter(
        Proyecto.id_proyecto == proyecto_id,
        Proyecto.user_id == user_id
    ).first()

    if not proyecto:
        return []

    return (
        db.query(RequerimientoFuncional)
        .filter(RequerimientoFuncional.proyecto_id == proyecto_id)
        .order_by(RequerimientoFuncional.codigo)
        .all()
    )


def get_rf_by_id(db: Session, id_req: int, user_id: int) -> RequerimientoFuncional | None:
    """Obtener un RF por ID (verificando que pertenezca al usuario)"""
    from app.models.proyecto import Proyecto

    rf = db.query(RequerimientoFuncional).filter(
        RequerimientoFuncional.id_req == id_req
    ).first()

    if not rf:
        return None

    # Verificar que el proyecto pertenezca al usuario
    proyecto = db.query(Proyecto).filter(
        Proyecto.id_proyecto == rf.proyecto_id,
        Proyecto.user_id == user_id
    ).first()

    return rf if proyecto else None


def update_rf(db: Session, rf: RequerimientoFuncional, data: RequerimientoFuncionalUpdate) -> RequerimientoFuncional:
    """Actualizar un requerimiento funcional"""
    if data.descripcion is not None:
        rf.descripcion = data.descripcion
    if data.actor is not None:
        rf.actor = data.actor
    if data.prioridad is not None:
        rf.prioridad = data.prioridad  # Ahora es string
    if data.estado is not None:
        rf.estado = data.estado  # Ahora es string

    db.commit()
    db.refresh(rf)
    return rf


def delete_rf(db: Session, rf: RequerimientoFuncional) -> None:
    """Eliminar un requerimiento funcional"""
    db.delete(rf)
    db.commit()


def get_rfs_resumen(db: Session, proyecto_id: int, user_id: int) -> RequerimientoFuncionalResumen:
    """Obtener resumen de RFs de un proyecto"""
    # Verificar que el proyecto pertenezca al usuario
    from app.models.proyecto import Proyecto
    proyecto = db.query(Proyecto).filter(
        Proyecto.id_proyecto == proyecto_id,
        Proyecto.user_id == user_id
    ).first()

    if not proyecto:
        return RequerimientoFuncionalResumen(total=0, completados=0, en_progreso=0, borradores=0)

    total = db.query(func.count(RequerimientoFuncional.id_req)).filter(
        RequerimientoFuncional.proyecto_id == proyecto_id
    ).scalar() or 0

    completados = db.query(func.count(RequerimientoFuncional.id_req)).filter(
        RequerimientoFuncional.proyecto_id == proyecto_id,
        RequerimientoFuncional.estado == "Completado"
    ).scalar() or 0

    en_progreso = db.query(func.count(RequerimientoFuncional.id_req)).filter(
        RequerimientoFuncional.proyecto_id == proyecto_id,
        RequerimientoFuncional.estado == "En progreso"
    ).scalar() or 0

    borradores = db.query(func.count(RequerimientoFuncional.id_req)).filter(
        RequerimientoFuncional.proyecto_id == proyecto_id,
        RequerimientoFuncional.estado == "Borrador"
    ).scalar() or 0

    return RequerimientoFuncionalResumen(
        total=total,
        completados=completados,
        en_progreso=en_progreso,
        borradores=borradores
    )