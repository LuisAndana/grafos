from sqlalchemy import Column, BigInteger, String, DateTime, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.core.database import Base


class TipoDiagrama(str, Enum):
    """Tipos de diagramas UML soportados"""
    CLASS = "class"
    SEQUENCE = "sequence"
    PACKAGE = "package"
    USECASE = "usecase"


class Diagrama(Base):
    __tablename__ = "diagramas"

    id_diagrama = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    id_proyecto = Column(BigInteger, ForeignKey("proyectos.id_proyecto"), nullable=False)
    nombre = Column(String(255), nullable=False)
    tipo = Column(SQLEnum(TipoDiagrama), nullable=False)
    descripcion = Column(Text, nullable=True)

    # Datos del diagrama (JSON serializado)
    elementos = Column(JSON, default=list)  # Lista de DiagramElement
    conexiones = Column(JSON, default=list)  # Lista de DiagramConnection
    vista_actual = Column(JSON, default=dict)  # ViewTransform

    # Metadatos
    id_usuario_creador = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    proyecto = relationship("Proyecto", foreign_keys=[id_proyecto])
    usuario_creador = relationship("User", foreign_keys=[id_usuario_creador])

    def __repr__(self):
        return f"<Diagrama {self.id_diagrama}: {self.nombre}>"
