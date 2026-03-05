from sqlalchemy import Column, BigInteger, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


# Los valores DEBEN coincidir EXACTAMENTE con lo que MySQL tiene en el ENUM
# MySQL tiene: 'Interno','Externo','Regulador','Proveedor','Otro'
# Por eso usamos Enum de SQLAlchemy directamente con strings, NO con Python enum

class Stakeholder(Base):
    __tablename__ = "stakeholders"

    id_stake         = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    proyecto_id      = Column(BigInteger, ForeignKey("proyectos.id_proyecto"), nullable=True)
    nombre           = Column(String(150), nullable=False)
    rol              = Column(String(150), nullable=False)
    tipo             = Column(
        Enum('Interno', 'Externo', 'Regulador', 'Proveedor', 'Otro', name='tipostakeholder'),
        nullable=False
    )
    area             = Column(String(100), nullable=False)
    nivel_influencia = Column(
        Enum('Alto', 'Medio', 'Bajo', name='nivelinfluencia'),
        nullable=False,
        default='Medio'
    )
    interes_sistema  = Column(Text, nullable=False)
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relación
    proyecto = relationship("Proyecto", back_populates="stakeholders")