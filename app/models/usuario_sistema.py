from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class UsuarioSistema(Base):
    __tablename__ = "usuarios_sistema"

    id_usuarios_sistema   = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    proyecto_id           = Column(BigInteger, ForeignKey("proyectos.id_proyecto"), nullable=True)
    tipo_id               = Column(BigInteger, ForeignKey("tipo_usuario_sistema.id_tipo"), nullable=True)
    nombre                = Column(String(150), nullable=False)
    descripcion_funciones = Column(Text, nullable=False)
    permisos_esperados    = Column(Text, nullable=False)
    created_at            = Column(DateTime, default=datetime.utcnow)
    updated_at            = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    proyecto = relationship("Proyecto", back_populates="usuarios_sistema")
    tipo     = relationship("TipoUsuarioSistema", back_populates="usuarios")