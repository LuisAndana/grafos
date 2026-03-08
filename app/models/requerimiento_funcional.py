# app/models/requerimiento_funcional.py
from sqlalchemy import Column, BigInteger, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class PrioridadReqFunc(str, enum.Enum):
    alta  = "Alta"
    media = "Media"
    baja  = "Baja"


class EstadoReqFunc(str, enum.Enum):
    borrador    = "Borrador"
    en_progreso = "En progreso"
    completado  = "Completado"


class RequerimientoFuncional(Base):
    __tablename__ = "requerimientos_funcionales"

    id_req      = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    proyecto_id = Column(BigInteger, ForeignKey("proyectos.id_proyecto"), nullable=True)
    codigo      = Column(String(20), nullable=False)
    descripcion = Column(Text, nullable=False)
    actor       = Column(String(150), nullable=True)

    # values_callable hace que SQLAlchemy use el .value ("Alta", "En progreso")
    # en lugar de la clave del enum ("alta", "en_progreso")
    prioridad = Column(
        Enum(PrioridadReqFunc, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=PrioridadReqFunc.media,
    )
    estado = Column(
        Enum(EstadoReqFunc, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=EstadoReqFunc.borrador,
    )

    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relación
    proyecto = relationship("Proyecto", back_populates="requerimientos_funcionales")