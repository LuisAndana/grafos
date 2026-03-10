from sqlalchemy import Column, BigInteger, String, Text, Date, DateTime, SmallInteger, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Observacion(Base):
    __tablename__ = "observaciones"

    id_observacion           = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    proyecto_id              = Column(BigInteger, ForeignKey("proyectos.id_proyecto"), nullable=True)
    fecha                    = Column(Date, nullable=False)
    lugar                    = Column(String(200), nullable=False)
    perfil_usuario_observado = Column(Text, nullable=False)
    # Checkboxes aspectos observados
    asp_interaccion_interfaz = Column(SmallInteger, nullable=False, default=0)
    asp_tiempo_respuesta     = Column(SmallInteger, nullable=False, default=0)
    asp_errores_dificultades = Column(SmallInteger, nullable=False, default=0)
    asp_patrones_navegacion  = Column(SmallInteger, nullable=False, default=0)
    asp_uso_funcionalidades  = Column(SmallInteger, nullable=False, default=0)
    asp_reacciones_usuario   = Column(SmallInteger, nullable=False, default=0)
    # Datos generales
    usuario_observado        = Column(String(150), nullable=True)
    usuario_area_rol         = Column(String(150), nullable=True)
    lugar_sistema            = Column(String(200), nullable=True)
    # Conclusiones
    conclusiones             = Column(Text, nullable=True)
    created_at               = Column(DateTime, default=datetime.utcnow)
    updated_at               = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)



class ObsFlujoPaso(Base):
    __tablename__ = "obs_flujo_pasos"

    id_obs_flujo   = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    observacion_id = Column(BigInteger, ForeignKey("observaciones.id_observacion"), nullable=False)
    numero_paso    = Column(SmallInteger, nullable=False)  # 1-5
    descripcion    = Column(String(300), nullable=False)

