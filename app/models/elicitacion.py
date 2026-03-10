from sqlalchemy import Column, BigInteger, String, Text, DateTime, SmallInteger, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class ElicitacionEntrevista(Base):
    __tablename__ = "elicitacion_entrevistas"

    id_entrevista = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    proyecto_id   = Column(BigInteger, ForeignKey("proyectos.id_proyecto"), nullable=True)
    pregunta      = Column(Text, nullable=False)
    respuesta     = Column(Text, nullable=True)
    observaciones = Column(Text, nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)




class ElicitacionProceso(Base):
    __tablename__ = "elicitacion_procesos"

    id_proceso           = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    proyecto_id          = Column(BigInteger, ForeignKey("proyectos.id_proyecto"), nullable=True)
    nombre_proceso       = Column(String(200), nullable=False)
    descripcion          = Column(Text, nullable=True)
    problemas_detectados = Column(Text, nullable=True)
    created_at           = Column(DateTime, default=datetime.utcnow)
    updated_at           = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)




class ElicitacionNecesidad(Base):
    __tablename__ = "elicitacion_necesidades"

    id_necesidad   = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    proyecto_id    = Column(BigInteger, ForeignKey("proyectos.id_proyecto"), nullable=True)
    nombre         = Column(String(200), nullable=False)   # "Gestión de usuarios", personalizada...
    es_predefinida = Column(SmallInteger, nullable=False, default=0)  # 1=checkbox del sistema
    seleccionada   = Column(SmallInteger, nullable=False, default=0)  # si está marcada
    created_at     = Column(DateTime, default=datetime.utcnow)

