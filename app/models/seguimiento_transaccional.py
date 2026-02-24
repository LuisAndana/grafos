from sqlalchemy import Column, BigInteger, String, Text, Date, DateTime, SmallInteger, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class SeguimientoTransaccional(Base):
    __tablename__ = "seguimiento_transaccional"

    id_seguimiento   = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    proyecto_id      = Column(BigInteger, ForeignKey("proyectos.id_proyecto"), nullable=True)
    # Datos Generales
    usuario_observado = Column(String(150), nullable=False)
    area_rol          = Column(String(150), nullable=False)
    fecha             = Column(Date, nullable=False)
    lugar_sistema     = Column(String(200), nullable=False)
    objetivo_proceso  = Column(Text, nullable=False)
    # Conclusiones
    conclusiones      = Column(Text, nullable=True)
    created_at        = Column(DateTime, default=datetime.utcnow)
    updated_at        = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    proyecto = relationship("Proyecto", back_populates="seguimientos_transaccional")
    pasos    = relationship("SegTransPaso", back_populates="seguimiento", cascade="all, delete-orphan")


class SegTransPaso(Base):
    __tablename__ = "seg_trans_pasos"

    id_paso        = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    seguimiento_id = Column(BigInteger, ForeignKey("seguimiento_transaccional.id_seguimiento"), nullable=False)
    numero_paso    = Column(SmallInteger, nullable=False)        # 1, 2, 3...
    descripcion    = Column(String(500), nullable=False)         # ¿Qué hace el usuario?
    observaciones  = Column(Text, nullable=True)                 # Notas, comportamientos, tiempo...

    # Relación
    seguimiento = relationship("SeguimientoTransaccional", back_populates="pasos")