from sqlalchemy import Column, BigInteger, String, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Proyecto(Base):
    __tablename__ = "proyectos"

    id_proyecto          = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id              = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    nombre               = Column(String(200), nullable=False)
    codigo               = Column(String(50), unique=True, nullable=False)
    descripcion_problema = Column(Text, nullable=False)
    objetivo_general     = Column(Text, nullable=False)
    fecha_inicio         = Column(Date, nullable=False)
    analista_responsable = Column(String(150), nullable=False)
    created_at           = Column(DateTime, default=datetime.utcnow)
    updated_at           = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    user             = relationship("User", back_populates="proyectos")
    stakeholders     = relationship("Stakeholder", back_populates="proyecto")
    usuarios_sistema = relationship("UsuarioSistema", back_populates="proyecto")
    focus_groups     = relationship("FocusGroup", back_populates="proyecto")
    observaciones    = relationship("Observacion", back_populates="proyecto")