from sqlalchemy import Column, BigInteger, String, SmallInteger, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class TipoUsuarioSistema(Base):
    __tablename__ = "tipo_usuario_sistema"

    id_tipo     = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    nombre      = Column(String(100), unique=True, nullable=False)
    descripcion = Column(String(255), nullable=True)
    activo      = Column(SmallInteger, nullable=False, default=1)  # 1=Activo, 0=Inactivo
    created_at  = Column(DateTime, default=datetime.utcnow)

    # Relación inversa
    usuarios = relationship("UsuarioSistema", back_populates="tipo")