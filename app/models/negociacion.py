from sqlalchemy import Column, BigInteger, String, Text, DateTime, SmallInteger, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class PrioridadNeg(str, enum.Enum):
    alta  = "Alta"
    media = "Media"
    baja  = "Baja"


class Negociacion(Base):
    __tablename__ = "negociacion"

    id_negociacion = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    proyecto_id    = Column(BigInteger, ForeignKey("proyectos.id_proyecto"), nullable=True)
    nombre         = Column(String(200), nullable=False)   # Nombre del Requerimiento
    descripcion    = Column(Text, nullable=False)
    prioridad      = Column(Enum(PrioridadNeg), nullable=False, default=PrioridadNeg.media)
    aceptado       = Column(SmallInteger, nullable=False, default=0)  # 0=No, 1=Sí
    created_at     = Column(DateTime, default=datetime.utcnow)
    updated_at     = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relación
    proyecto = relationship("Proyecto", back_populates="negociaciones")