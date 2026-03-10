# app/models/requerimiento_funcional.py
from sqlalchemy import Column, BigInteger, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class PrioridadReqFunc(str, enum.Enum):
    """Prioridad - valores tal como están en la BD"""
    alta = "Alta"
    media = "Media"
    baja = "Baja"


class EstadoReqFunc(str, enum.Enum):
    """Estado - valores tal como están en la BD"""
    borrador = "Borrador"
    en_progreso = "En progreso"
    completado = "Completado"


class RequerimientoFuncional(Base):
    __tablename__ = "requerimientos_funcionales"

    id_req      = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    proyecto_id = Column(BigInteger, ForeignKey("proyectos.id_proyecto"), nullable=True)
    codigo      = Column(String(20), nullable=False)       # RF-001, RF-002...
    descripcion = Column(Text, nullable=False)
    actor       = Column(String(150), nullable=True)
    # native_enum=False hace que SQLAlchemy no valide contra el enum de MySQL
    # Esto permite leer datos que no coincidan exactamente con los valores del enum
    prioridad = Column(String(50), default='Media')
    estado = Column(String(50), default='Borrador')
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

