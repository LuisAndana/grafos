# app/services/negociacion_service.py
from sqlalchemy.orm import Session
from app.models.negociacion import Negociacion
from app.schemas.negociacion_schema import NegociacionCreate, NegociacionUpdate


class NegociacionService:

    @staticmethod
    def get_negociaciones_by_proyecto(db: Session, proyecto_id: int):
        """Obtiene todas las negociaciones de un proyecto"""
        try:
            negociaciones = db.query(Negociacion).filter(
                Negociacion.proyecto_id == proyecto_id
            ).order_by(Negociacion.created_at.desc()).all()

            return [
                {
                    "id_negociacion": n.id_negociacion,
                    "proyecto_id": n.proyecto_id,
                    "nombre": n.nombre,
                    "descripcion": n.descripcion,
                    "prioridad": n.prioridad,
                    "aceptado": n.aceptado,
                    "created_at": n.created_at,
                    "updated_at": n.updated_at,
                }
                for n in negociaciones
            ]
        except Exception as e:
            print(f"Error en get_negociaciones_by_proyecto: {str(e)}")
            raise e

    @staticmethod
    def get_negociacion_by_id(db: Session, negociacion_id: int):
        """Obtiene una negociación específica"""
        try:
            negociacion = db.query(Negociacion).filter(
                Negociacion.id_negociacion == negociacion_id
            ).first()

            if not negociacion:
                return None

            return {
                "id_negociacion": negociacion.id_negociacion,
                "proyecto_id": negociacion.proyecto_id,
                "nombre": negociacion.nombre,
                "descripcion": negociacion.descripcion,
                "prioridad": negociacion.prioridad,
                "aceptado": negociacion.aceptado,
                "created_at": negociacion.created_at,
                "updated_at": negociacion.updated_at,
            }
        except Exception as e:
            print(f"Error en get_negociacion_by_id: {str(e)}")
            raise e

    @staticmethod
    def create_negociacion(db: Session, negociacion: NegociacionCreate):
        """Crea una nueva negociación"""
        try:
            new_negociacion = Negociacion(
                proyecto_id=negociacion.proyecto_id,
                nombre=negociacion.nombre,
                descripcion=negociacion.descripcion,
                prioridad=negociacion.prioridad or 'Media',
                aceptado=negociacion.aceptado or 0
            )
            db.add(new_negociacion)
            db.commit()
            db.refresh(new_negociacion)

            return {
                "id_negociacion": new_negociacion.id_negociacion,
                "proyecto_id": new_negociacion.proyecto_id,
                "nombre": new_negociacion.nombre,
                "descripcion": new_negociacion.descripcion,
                "prioridad": new_negociacion.prioridad,
                "aceptado": new_negociacion.aceptado,
                "created_at": new_negociacion.created_at,
                "updated_at": new_negociacion.updated_at,
            }
        except Exception as e:
            db.rollback()
            print(f"Error en create_negociacion: {str(e)}")
            raise e

    @staticmethod
    def update_negociacion(db: Session, negociacion_id: int, negociacion: NegociacionUpdate):
        """Actualiza una negociación"""
        try:
            existing = db.query(Negociacion).filter(
                Negociacion.id_negociacion == negociacion_id
            ).first()

            if not existing:
                return None

            if negociacion.nombre is not None:
                existing.nombre = negociacion.nombre
            if negociacion.descripcion is not None:
                existing.descripcion = negociacion.descripcion
            if negociacion.prioridad is not None:
                existing.prioridad = negociacion.prioridad
            if negociacion.aceptado is not None:
                existing.aceptado = negociacion.aceptado

            db.commit()
            db.refresh(existing)

            return {
                "id_negociacion": existing.id_negociacion,
                "proyecto_id": existing.proyecto_id,
                "nombre": existing.nombre,
                "descripcion": existing.descripcion,
                "prioridad": existing.prioridad,
                "aceptado": existing.aceptado,
                "created_at": existing.created_at,
                "updated_at": existing.updated_at,
            }
        except Exception as e:
            db.rollback()
            print(f"Error en update_negociacion: {str(e)}")
            raise e

    @staticmethod
    def delete_negociacion(db: Session, negociacion_id: int):
        """Elimina una negociación"""
        try:
            negociacion = db.query(Negociacion).filter(
                Negociacion.id_negociacion == negociacion_id
            ).first()

            if not negociacion:
                return False

            db.delete(negociacion)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Error en delete_negociacion: {str(e)}")
            raise e

    @staticmethod
    def get_negociaciones_resumen(db: Session, proyecto_id: int):
        """Obtiene un resumen de negociaciones por estado"""
        try:
            negociaciones = db.query(Negociacion).filter(
                Negociacion.proyecto_id == proyecto_id
            ).all()

            total = len(negociaciones)
            aceptadas = len([n for n in negociaciones if n.aceptado == 1])
            pendientes = total - aceptadas

            return {
                "total": total,
                "aceptadas": aceptadas,
                "pendientes": pendientes
            }
        except Exception as e:
            print(f"Error en get_negociaciones_resumen: {str(e)}")
            raise e