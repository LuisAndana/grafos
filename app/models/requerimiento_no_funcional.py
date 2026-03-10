# app/models/requerimiento_no_funcional.py
from sqlalchemy import Column, BigInteger, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class TipoRNF(str, enum.Enum):
    seguridad = "Seguridad"
    rendimiento = "Rendimiento"
    usabilidad = "Usabilidad"
    compatibilidad = "Compatibilidad"
    otro = "Otro"


class RequerimientoNoFuncional(Base):
    __tablename__ = "requerimientos_no_funcionales"

    id_rnf      = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    proyecto_id = Column(BigInteger, ForeignKey("proyectos.id_proyecto"), nullable=False)
    codigo      = Column(String(20), nullable=False)       # RNF-001, RNF-002...
    tipo        = Column(Enum(TipoRNF), nullable=False, default=TipoRNF.otro)
    descripcion = Column(Text, nullable=False)
    metrica     = Column(String(255), nullable=True)       # "Tiempo respuesta ≤ 2 seg"
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
