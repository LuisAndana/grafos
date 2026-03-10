# app/models/negociacion.py
from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey, Integer
from datetime import datetime
from app.core.database import Base


class Negociacion(Base):
    __tablename__ = "negociacion"

    id_negociacion = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    proyecto_id = Column(BigInteger, ForeignKey("proyectos.id_proyecto"), nullable=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=False)
    prioridad = Column(String(50), nullable=False, default='Media')
    aceptado = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)