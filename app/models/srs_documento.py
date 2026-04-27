# app/models/srs_documento.py
from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey, JSON
from datetime import datetime
from app.core.database import Base


class SrsDocumento(Base):
    __tablename__ = "srs_documentos"

    id_srs = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    proyecto_id = Column(BigInteger, ForeignKey("proyectos.id_proyecto"), nullable=False)
    nombre_documento = Column(String(255), nullable=False)
    generado_por = Column(BigInteger, nullable=True, default=None)  # FK optional
    introduccion = Column(Text, nullable=True)

    # Stakeholders (almacenado como JSON)
    stakeholders = Column(JSON, nullable=True, default=list)

    # Usuarios (almacenado como JSON)
    usuarios = Column(JSON, nullable=True, default=list)

    # Requerimientos funcionales (almacenado como JSON)
    requerimientos_funcionales = Column(JSON, nullable=True, default=list)

    # Requerimientos no funcionales (almacenado como JSON)
    requerimientos_no_funcionales = Column(JSON, nullable=True, default=list)

    # Casos de uso (almacenado como JSON)
    casos_uso = Column(JSON, nullable=True, default=list)

    # Restricciones (almacenado como JSON)
    restricciones = Column(JSON, nullable=True, default=list)

    # ── Nuevas secciones (auto-generadas desde los módulos del proyecto) ──
    # Elicitación: {"entrevistas": [...], "procesos": [...], "necesidades": [...]}
    elicitacion = Column(JSON, nullable=True, default=dict)

    # Negociaciones: [{nombre, descripcion, prioridad, aceptado}, ...]
    negociaciones = Column(JSON, nullable=True, default=list)

    # Validación: {aprobado, aprobador, observaciones, checklist_*}
    validacion_info = Column(JSON, nullable=True, default=dict)

    # Artefactos: [{nombre, categoria, descripcion, nombre_archivo, tipo_mime}, ...]
    artefactos_info = Column(JSON, nullable=True, default=list)

    # Metadata
    estado = Column(String(50), default='Borrador')  # Borrador, Completo, Aprobado
    version = Column(String(20), default='1.0')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)