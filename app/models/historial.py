from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Historial(Base):
    __tablename__ = "historial"

    id_historial = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id      = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    proyecto_id  = Column(BigInteger, ForeignKey("proyectos.id_proyecto"), nullable=True)
    accion       = Column(String(100), nullable=False)   # "Creó proyecto", "Agregó RF"...
    modulo       = Column(String(100), nullable=False)   # "proyectos", "requerimientos"...
    descripcion  = Column(Text, nullable=True)
    fecha        = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    user     = relationship("User", back_populates="historial")
    proyecto = relationship("Proyecto", back_populates="historial")