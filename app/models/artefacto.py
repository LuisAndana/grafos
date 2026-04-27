from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey
from datetime import datetime
from app.core.database import Base


class Artefacto(Base):
    __tablename__ = "artefactos"

    id_artefacto   = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    proyecto_id    = Column(BigInteger, ForeignKey("proyectos.id_proyecto"), nullable=False)
    nombre         = Column(String(200), nullable=False)
    categoria      = Column(String(100), nullable=False)
    descripcion    = Column(Text, nullable=True)
    nombre_archivo = Column(String(255), nullable=False)
    ruta_archivo   = Column(String(500), nullable=False)
    tipo_mime      = Column(String(100), nullable=False)
    tamanio        = Column(BigInteger, nullable=False)
    created_at     = Column(DateTime, default=datetime.utcnow)
    updated_at     = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
