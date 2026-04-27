from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.historial import Historial
from app.models.proyecto import Proyecto
from app.models.stakeholder import Stakeholder
from app.models.requerimiento_funcional import RequerimientoFuncional
from app.models.requerimiento_no_funcional import RequerimientoNoFuncional
from app.models.tipo_usuario_proyecto import TipoUsuarioProyecto
from app.models.caso_uso import CasoUso
from app.models.restriccion import Restriccion
from app.models.validacion import Validacion
from app.schemas.historial_schema import HistorialCreate


def _verificar_proyecto(db: Session, proyecto_id: int) -> Proyecto:
    proyecto = db.query(Proyecto).filter(Proyecto.id_proyecto == proyecto_id).first()
    if not proyecto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado.",
        )
    return proyecto


# ── CRUD básico ───────────────────────────────────────────────────────────────

def get_historial(db: Session, proyecto_id: int) -> list[Historial]:
    _verificar_proyecto(db, proyecto_id)
    return (
        db.query(Historial)
        .filter(Historial.proyecto_id == proyecto_id)
        .order_by(Historial.fecha.desc())
        .all()
    )


def create_entrada(db: Session, data: HistorialCreate) -> Historial:
    _verificar_proyecto(db, data.proyecto_id)

    entrada = Historial(
        proyecto_id=data.proyecto_id,
        accion=data.accion,
        modulo=data.modulo,
        detalles=data.detalles,
        es_snapshot=data.es_snapshot,
    )
    db.add(entrada)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar historial: {str(e)}",
        )
    db.refresh(entrada)
    return entrada


def delete_historial(db: Session, proyecto_id: int) -> dict:
    _verificar_proyecto(db, proyecto_id)
    eliminados = (
        db.query(Historial)
        .filter(Historial.proyecto_id == proyecto_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return {"detail": f"{eliminados} entradas de historial eliminadas."}


# ── Snapshot ──────────────────────────────────────────────────────────────────

def _proyecto_to_dict(p: Proyecto) -> dict:
    return {
        "id_proyecto":         p.id_proyecto,
        "nombre":              p.nombre,
        "codigo":              p.codigo,
        "descripcion_problema": p.descripcion_problema,
        "objetivo_general":    p.objetivo_general,
        "fecha_inicio":        str(p.fecha_inicio) if p.fecha_inicio else None,
        "analista_responsable": p.analista_responsable,
    }


def _stakeholder_to_dict(s: Stakeholder) -> dict:
    return {
        "id_stake":         s.id_stake,
        "nombre":           s.nombre,
        "rol":              s.rol,
        "tipo":             str(s.tipo.value) if hasattr(s.tipo, "value") else s.tipo,
        "area":             s.area,
        "nivel_influencia": str(s.nivel_influencia.value) if hasattr(s.nivel_influencia, "value") else s.nivel_influencia,
        "interes_sistema":  s.interes_sistema,
    }


def _rf_to_dict(r: RequerimientoFuncional) -> dict:
    return {
        "id_req":      r.id_req,
        "codigo":      r.codigo,
        "descripcion": r.descripcion,
        "actor":       r.actor,
        "prioridad":   r.prioridad,
        "estado":      r.estado,
    }


def _rnf_to_dict(r: RequerimientoNoFuncional) -> dict:
    return {
        "id_rnf":      r.id_rnf,
        "codigo":      r.codigo,
        "descripcion": r.descripcion,
        "tipo":        str(r.tipo.value) if hasattr(r.tipo, "value") else r.tipo,
        "metrica":     r.metrica,
    }


def _tipo_usuario_to_dict(t: TipoUsuarioProyecto) -> dict:
    return {
        "id_tipo_usuario": t.id_tipo_usuario,
        "tipo":            t.tipo,
        "descripcion":     t.descripcion,
    }


def _caso_uso_to_dict(c: CasoUso) -> dict:
    return {
        "id_caso_uso": c.id_caso_uso,
        "nombre":      c.nombre,
        "actores":     c.actores,
        "descripcion": c.descripcion,
        "pasos":       c.pasos,
    }


def _restriccion_to_dict(r: Restriccion) -> dict:
    return {
        "id_restriccion": r.id_restriccion,
        "codigo":         r.codigo,
        "tipo":           r.tipo,
        "descripcion":    r.descripcion,
    }


def _validacion_to_dict(v: Validacion) -> dict:
    return {
        "id_validacion":          v.id_validacion,
        "checklist_rf":           v.checklist_rf,
        "checklist_rnf":          v.checklist_rnf,
        "checklist_casos_uso":    v.checklist_casos_uso,
        "checklist_restricciones": v.checklist_restricciones,
        "checklist_prioridades":  v.checklist_prioridades,
        "observaciones":          v.observaciones,
        "aprobador":              v.aprobador,
        "fecha":                  str(v.fecha) if v.fecha else None,
        "firma_digital":          v.firma_digital,
        "aprobado":               v.aprobado,
    }


def create_snapshot(db: Session, proyecto_id: int) -> Historial:
    proyecto = _verificar_proyecto(db, proyecto_id)

    stakeholders = db.query(Stakeholder).filter(Stakeholder.proyecto_id == proyecto_id).all()
    rfs          = db.query(RequerimientoFuncional).filter(RequerimientoFuncional.proyecto_id == proyecto_id).all()
    rnfs         = db.query(RequerimientoNoFuncional).filter(RequerimientoNoFuncional.proyecto_id == proyecto_id).all()
    tipos_usuario = db.query(TipoUsuarioProyecto).filter(TipoUsuarioProyecto.proyecto_id == proyecto_id).all()
    casos_uso    = db.query(CasoUso).filter(CasoUso.proyecto_id == proyecto_id).all()
    restricciones = db.query(Restriccion).filter(Restriccion.proyecto_id == proyecto_id).all()
    validacion   = db.query(Validacion).filter(Validacion.proyecto_id == proyecto_id).first()

    detalles = {
        "fecha_snapshot":    datetime.utcnow().isoformat(),
        "proyecto":          _proyecto_to_dict(proyecto),
        "stakeholders":      [_stakeholder_to_dict(s) for s in stakeholders],
        "requerimientos_funcionales":     [_rf_to_dict(r) for r in rfs],
        "requerimientos_no_funcionales":  [_rnf_to_dict(r) for r in rnfs],
        "tipos_usuario":     [_tipo_usuario_to_dict(t) for t in tipos_usuario],
        "casos_uso":         [_caso_uso_to_dict(c) for c in casos_uso],
        "restricciones":     [_restriccion_to_dict(r) for r in restricciones],
        "validacion":        _validacion_to_dict(validacion) if validacion else None,
        "resumen": {
            "total_stakeholders": len(stakeholders),
            "total_rf":           len(rfs),
            "total_rnf":          len(rnfs),
            "total_tipos_usuario": len(tipos_usuario),
            "total_casos_uso":    len(casos_uso),
            "total_restricciones": len(restricciones),
            "validado":           validacion.aprobado if validacion else False,
        },
    }

    snapshot = Historial(
        proyecto_id=proyecto_id,
        accion=f'Snapshot del proyecto "{proyecto.nombre}"',
        modulo="Snapshot",
        detalles=detalles,
        es_snapshot=True,
    )
    db.add(snapshot)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear snapshot: {str(e)}",
        )
    db.refresh(snapshot)
    return snapshot
