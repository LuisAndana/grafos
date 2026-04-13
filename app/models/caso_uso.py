from sqlalchemy import Column, BigInteger, String, Text, DateTime, JSON, ForeignKey
from datetime import datetime
from app.core.database import Base


class CasoUso(Base):
    __tablename__ = "casos_uso"

    id_caso_uso = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    proyecto_id = Column(BigInteger, ForeignKey("proyectos.id_proyecto"), nullable=False)
    nombre      = Column(String(200), nullable=False)
    actores     = Column(JSON, nullable=True, default=list)
    descripcion = Column(Text, nullable=True)
    pasos       = Column(JSON, nullable=True, default=list)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
