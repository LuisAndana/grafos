from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey
from datetime import datetime
from app.core.database import Base


class TipoUsuarioProyecto(Base):
    __tablename__ = "tipo_usuario_proyecto"

    id_tipo_usuario = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    proyecto_id     = Column(BigInteger, ForeignKey("proyectos.id_proyecto"), nullable=False)
    tipo            = Column(String(150), nullable=False)
    descripcion     = Column(Text, nullable=True)
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
