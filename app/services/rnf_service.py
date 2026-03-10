# app/services/rnf_service.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.models.requerimiento_no_funcional import RequerimientoNoFuncional
from app.models.proyecto import Proyecto
from app.schemas.rnf_schema import RNFCreate, RNFUpdate, RNFResumen


def _verificar_proyecto_del_usuario(db: Session, proyecto_id: int, user_id: int) -> Proyecto:
    """Verifica que el proyecto exista y pertenezca al usuario."""
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


def _generar_codigo(db: Session, proyecto_id: int) -> str:
    """Genera el próximo código RNF-XXX para el proyecto."""
    ultima_rnf = (
        db.query(RequerimientoNoFuncional)
        .filter(RequerimientoNoFuncional.proyecto_id == proyecto_id)
        .order_by(RequerimientoNoFuncional.id_rnf.desc())
        .first()
    )

    if ultima_rnf:
        # Extraer número del código anterior (ej: "RNF-003" → 3)
        numero = int(ultima_rnf.codigo.split('-')[1]) + 1
    else:
        numero = 1

    return f"RNF-{numero:03d}"


# ─────────────────────────────────────────────
# CREATE
# ─────────────────────────────────────────────

def create_rnf(db: Session, data: RNFCreate, user_id: int) -> RequerimientoNoFuncional:
    """Crea un nuevo requerimiento no funcional."""
    # Verificar que el proyecto pertenezca al usuario
    _verificar_proyecto_del_usuario(db, data.proyecto_id, user_id)

    # Generar código automático
    codigo = _generar_codigo(db, data.proyecto_id)

    rnf = RequerimientoNoFuncional(
        proyecto_id=data.proyecto_id,
        codigo=codigo,
        tipo=data.tipo,
        descripcion=data.descripcion,
        metrica=data.metrica,
    )

    db.add(rnf)
    try:
        db.commit()
        db.refresh(rnf)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Error al guardar el requerimiento.",
        )

    return rnf


# ─────────────────────────────────────────────
# READ
# ─────────────────────────────────────────────

def get_rnfs_by_proyecto(db: Session, proyecto_id: int, user_id: int) -> list[RequerimientoNoFuncional]:
    """Obtiene todos los RNF de un proyecto."""
    _verificar_proyecto_del_usuario(db, proyecto_id, user_id)

    return (
        db.query(RequerimientoNoFuncional)
        .filter(RequerimientoNoFuncional.proyecto_id == proyecto_id)
        .order_by(RequerimientoNoFuncional.created_at.desc())
        .all()
    )


def get_rnf(db: Session, rnf_id: int, user_id: int) -> RequerimientoNoFuncional:
    """Obtiene un RNF específico."""
    rnf = db.query(RequerimientoNoFuncional).filter(
        RequerimientoNoFuncional.id_rnf == rnf_id
    ).first()

    if not rnf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requerimiento no encontrado.",
        )

    # Verificar que pertenezca al usuario
    _verificar_proyecto_del_usuario(db, rnf.proyecto_id, user_id)

    return rnf


# ─────────────────────────────────────────────
# UPDATE
# ─────────────────────────────────────────────

def update_rnf(
        db: Session, rnf_id: int, data: RNFUpdate, user_id: int
) -> RequerimientoNoFuncional:
    """Actualiza un RNF."""
    rnf = get_rnf(db, rnf_id, user_id)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rnf, field, value)

    try:
        db.commit()
        db.refresh(rnf)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Error al actualizar el requerimiento.",
        )

    return rnf


# ─────────────────────────────────────────────
# DELETE
# ─────────────────────────────────────────────

def delete_rnf(db: Session, rnf_id: int, user_id: int) -> dict:
    """Elimina un RNF."""
    rnf = get_rnf(db, rnf_id, user_id)
    codigo = rnf.codigo

    db.delete(rnf)
    db.commit()

    return {"detail": f"Requerimiento '{codigo}' eliminado correctamente."}


# ─────────────────────────────────────────────
# RESUMEN
# ─────────────────────────────────────────────

def get_resumen_rnf(db: Session, proyecto_id: int, user_id: int) -> RNFResumen:
    """Obtiene un resumen de RNF del proyecto."""
    _verificar_proyecto_del_usuario(db, proyecto_id, user_id)

    rnfs = get_rnfs_by_proyecto(db, proyecto_id, user_id)

    por_tipo = {}
    for rnf in rnfs:
        tipo = rnf.tipo
        por_tipo[tipo] = por_tipo.get(tipo, 0) + 1

    return RNFResumen(
        total=len(rnfs),
        por_tipo=por_tipo,
    )