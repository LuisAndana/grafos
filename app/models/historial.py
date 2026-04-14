from sqlalchemy import Column, BigInteger, String, DateTime, Boolean, JSON, ForeignKey
from datetime import datetime
from app.core.database import Base


class Historial(Base):
    __tablename__ = "historial"

    id_historial = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    proyecto_id  = Column(BigInteger, ForeignKey("proyectos.id_proyecto"), nullable=False)
    accion       = Column(String(200), nullable=False)
    modulo       = Column(String(100), nullable=False)
    detalles     = Column(JSON, nullable=True)
    es_snapshot  = Column(Boolean, nullable=False, default=False)
    fecha        = Column(DateTime, default=datetime.utcnow)
