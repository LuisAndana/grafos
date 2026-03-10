from sqlalchemy import Column, BigInteger, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Proyecto(Base):
    __tablename__ = "proyectos"

    id_proyecto = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    nombre = Column(String(255), nullable=False)
    codigo = Column(String(50), unique=True, nullable=False)
    descripcion_problema = Column(Text, nullable=True)
    objetivo_general = Column(Text, nullable=True)
    fecha_inicio = Column(DateTime, nullable=True)
    analista_responsable = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

