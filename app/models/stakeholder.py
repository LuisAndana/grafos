from sqlalchemy import Column, BigInteger, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class TipoStakeholder(str, enum.Enum):
    interno   = "Interno"
    externo   = "Externo"
    regulador = "Regulador"
    proveedor = "Proveedor"
    otro      = "Otro"


class NivelInfluencia(str, enum.Enum):
    alto  = "Alto"
    medio = "Medio"
    bajo  = "Bajo"


class Stakeholder(Base):
    __tablename__ = "stakeholders"

    id_stake         = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    proyecto_id      = Column(BigInteger, ForeignKey("proyectos.id_proyecto"), nullable=True)
    nombre           = Column(String(150), nullable=False)
    rol              = Column(String(150), nullable=False)
    tipo             = Column(Enum(TipoStakeholder), nullable=False)
    area             = Column(String(100), nullable=False)
    nivel_influencia = Column(Enum(NivelInfluencia), nullable=False, default=NivelInfluencia.medio)
    interes_sistema  = Column(Text, nullable=False)
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relación
    proyecto = relationship("Proyecto", back_populates="stakeholders")