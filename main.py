# -*- coding: utf-8 -*-
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine
from app.core.config import get_settings

# Modelos
from app.models.user import User
from app.models.proyecto import Proyecto
from app.models.historial import Historial
from app.models.srs_documento import SrsDocumento
from app.models.elicitacion import ElicitacionEntrevista, ElicitacionProceso, ElicitacionNecesidad
from app.models.focus_group import FocusGroup
from app.models.negociacion import Negociacion
from app.models.observacion import Observacion
from app.models.requerimiento_funcional import RequerimientoFuncional
from app.models.seguimiento_transaccional import SeguimientoTransaccional
from app.models.stakeholder import Stakeholder
from app.models.tipo_usuario_sistema import TipoUsuarioSistema
from app.models.usuario_sistema import UsuarioSistema
from app.models.validacion import Validacion

from app.routes.auth import router

settings = get_settings()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Backend API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
async def root():
    return {"message": "API en funcionamiento", "docs": "/docs"}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=settings.debug)