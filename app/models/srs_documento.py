from sqlalchemy import Column, BigInteger, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class SrsDocumento(Base):
    __tablename__ = "srs_documentos"

    id_srs           = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    proyecto_id      = Column(BigInteger, ForeignKey("proyectos.id_proyecto"), nullable=False)
    generado_por     = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    introduccion     = Column(Text, nullable=True)
    fecha_generacion = Column(DateTime, nullable=True)   # None = todavía no se ha generado PDF
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    proyecto    = relationship("Proyecto", back_populates="srs_documentos")
    generado_by = relationship("User", back_populates="srs_documentos")