from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey
from datetime import datetime
from app.core.database import Base


class Restriccion(Base):
    __tablename__ = "restricciones"

    id_restriccion = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    proyecto_id    = Column(BigInteger, ForeignKey("proyectos.id_proyecto"), nullable=False)
    codigo         = Column(String(50), nullable=False)
    tipo           = Column(String(100), nullable=False)
    descripcion    = Column(Text, nullable=True)
    created_at     = Column(DateTime, default=datetime.utcnow)
    updated_at     = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
