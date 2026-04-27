from sqlalchemy import Column, BigInteger, String, Text, Date, DateTime, Boolean, ForeignKey, UniqueConstraint
from datetime import datetime
from app.core.database import Base


class Validacion(Base):
    __tablename__ = "validacion"
    __table_args__ = (
        UniqueConstraint("proyecto_id", name="uq_validacion_proyecto"),
    )

    id_validacion         = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    proyecto_id           = Column(BigInteger, ForeignKey("proyectos.id_proyecto"), nullable=False)
    # Checklist
    checklist_rf          = Column(Boolean, nullable=False, default=False)
    checklist_rnf         = Column(Boolean, nullable=False, default=False)
    checklist_casos_uso   = Column(Boolean, nullable=False, default=False)
    checklist_restricciones = Column(Boolean, nullable=False, default=False)
    checklist_prioridades = Column(Boolean, nullable=False, default=False)
    # Observaciones y aprobación
    observaciones         = Column(Text, nullable=True)
    aprobador             = Column(String(150), nullable=True)
    fecha                 = Column(Date, nullable=True)
    firma_digital         = Column(String(255), nullable=True)
    aprobado              = Column(Boolean, nullable=False, default=False)
    # Timestamps
    created_at            = Column(DateTime, default=datetime.utcnow)
    updated_at            = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
