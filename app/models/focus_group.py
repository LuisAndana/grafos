from sqlalchemy import Column, BigInteger, String, Text, Date, DateTime, SmallInteger, Integer, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class EstadoFocusGroup(str, enum.Enum):
    planificado = "Planificado"
    en_curso    = "En curso"
    completado  = "Completado"
    cancelado   = "Cancelado"


class RolParticipante(str, enum.Enum):
    stakeholder = "Stakeholder"
    usuario     = "Usuario"
    analista    = "Analista"
    observador  = "Observador"
    otro        = "Otro"


class NivelInfluenciaFG(str, enum.Enum):
    alto  = "Alto"
    medio = "Medio"
    bajo  = "Bajo"


class PrioridadReq(str, enum.Enum):
    alto  = "Alto"
    medio = "Medio"
    bajo  = "Bajo"


class CategoriaReq(str, enum.Enum):
    funcional    = "Funcional"
    no_funcional = "No Funcional"
    restriccion  = "Restricción"
    otro         = "Otro"


class FocusGroup(Base):
    __tablename__ = "focus_groups"

    id_focus         = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    proyecto_id      = Column(BigInteger, ForeignKey("proyectos.id_proyecto"), nullable=True)
    nombre_taller    = Column(String(200), nullable=False)
    fecha            = Column(Date, nullable=False)
    duracion_minutos = Column(Integer, nullable=False)
    moderador        = Column(String(150), nullable=False)
    ubicacion_sala   = Column(String(200), nullable=False)
    estado           = Column(Enum(EstadoFocusGroup), nullable=False, default=EstadoFocusGroup.planificado)
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    proyecto       = relationship("Proyecto", back_populates="focus_groups")
    participantes  = relationship("FgParticipante",  back_populates="focus_group", cascade="all, delete-orphan")
    objetivos      = relationship("FgObjetivo",      back_populates="focus_group", cascade="all, delete-orphan")
    requerimientos = relationship("FgRequerimiento", back_populates="focus_group", cascade="all, delete-orphan")


class FgParticipante(Base):
    __tablename__ = "fg_participantes"

    id_fg_participante = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    focus_group_id     = Column(BigInteger, ForeignKey("focus_groups.id_focus"), nullable=False)
    nombre             = Column(String(150), nullable=False)
    rol                = Column(Enum(RolParticipante), nullable=False, default=RolParticipante.stakeholder)
    area               = Column(String(100), nullable=False)
    email              = Column(String(200), nullable=False)
    nivel_influencia   = Column(Enum(NivelInfluenciaFG), nullable=False, default=NivelInfluenciaFG.medio)

    # Relación
    focus_group = relationship("FocusGroup", back_populates="participantes")


class FgObjetivo(Base):
    __tablename__ = "fg_objetivos"

    id_fg_objetivo = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    focus_group_id = Column(BigInteger, ForeignKey("focus_groups.id_focus"), nullable=False)
    descripcion    = Column(Text, nullable=False)
    es_principal   = Column(SmallInteger, nullable=False, default=0)  # 0 = No, 1 = Sí

    # Relación
    focus_group = relationship("FocusGroup", back_populates="objetivos")


class FgRequerimiento(Base):
    __tablename__ = "fg_requerimientos"

    id_fg_requerimiento = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    focus_group_id      = Column(BigInteger, ForeignKey("focus_groups.id_focus"), nullable=False)
    codigo              = Column(String(20), nullable=False)   # REQ-001, REQ-002 ...
    descripcion         = Column(Text, nullable=False)
    prioridad           = Column(Enum(PrioridadReq), nullable=False, default=PrioridadReq.medio)
    categoria           = Column(Enum(CategoriaReq), nullable=False, default=CategoriaReq.funcional)

    # Relación
    focus_group = relationship("FocusGroup", back_populates="requerimientos")