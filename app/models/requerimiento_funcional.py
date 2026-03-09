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
    codigo      = Column(String(20), nullable=False)       # RF-001, RF-002...
    descripcion = Column(Text, nullable=False)
    actor       = Column(String(150), nullable=True)
    prioridad   = Column(Enum(PrioridadReqFunc), nullable=False, default=PrioridadReqFunc.media)
    estado      = Column(Enum(EstadoReqFunc), nullable=False, default=EstadoReqFunc.borrador)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relación
    proyecto = relationship("Proyecto", back_populates="requerimientos_funcionales")