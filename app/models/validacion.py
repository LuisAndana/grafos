from sqlalchemy import Column, BigInteger, String, Text, Date, DateTime, SmallInteger, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base

class EstadoValidacion(str, enum.Enum):
    pendiente = "Pendiente"
    validado  = "Validado"
    rechazado = "Rechazado"


class Validacion(Base):
    __tablename__ = "validacion"

    id_validacion            = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    proyecto_id              = Column(BigInteger, ForeignKey("proyectos.id_proyecto"), nullable=True)
    # Checklist de Revisión
    check_req_funcionales    = Column(SmallInteger, nullable=False, default=0)
    check_req_no_funcionales = Column(SmallInteger, nullable=False, default=0)
    check_casos_uso          = Column(SmallInteger, nullable=False, default=0)
    check_restricciones      = Column(SmallInteger, nullable=False, default=0)
    check_priorizacion       = Column(SmallInteger, nullable=False, default=0)
    # Observaciones
    observaciones_cliente    = Column(Text, nullable=True)
    # Datos de Aprobación
    nombre_aprobador         = Column(String(150), nullable=True)
    fecha_aprobacion         = Column(Date, nullable=True)
    firma_digital            = Column(String(255), nullable=True)
    # Estado
    estado                   = Column(Enum(EstadoValidacion), nullable=False, default=EstadoValidacion.pendiente)
    created_at               = Column(DateTime, default=datetime.utcnow)
    updated_at               = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

