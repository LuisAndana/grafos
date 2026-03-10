from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from app.core.database import Base, engine
from app.core.config import get_settings

# ════════════════════════════════════════════════════════════════════════════
# MODELOS
# ════════════════════════════════════════════════════════════════════════════

from app.models.user import User
from app.models.proyecto import Proyecto
from app.models.historial import Historial
from app.models.srs_documento import SrsDocumento
from app.models.elicitacion import ElicitacionEntrevista, ElicitacionProceso, ElicitacionNecesidad
from app.models.focus_group import FocusGroup
from app.models.negociacion import Negociacion
from app.models.observacion import Observacion
from app.models.requerimiento_funcional import RequerimientoFuncional
from app.models.requerimiento_no_funcional import RequerimientoNoFuncional
from app.models.seguimiento_transaccional import SeguimientoTransaccional
from app.models.stakeholder import Stakeholder
from app.models.tipo_usuario_sistema import TipoUsuarioSistema
from app.models.usuario_sistema import UsuarioSistema
from app.models.validacion import Validacion

# ════════════════════════════════════════════════════════════════════════════
# ROUTERS
# ════════════════════════════════════════════════════════════════════════════

from app.routes.auth import router
from app.routes.proyecto_router import router as proyecto_router
from app.routes.stakeholder_router import router as stakeholder_router
from app.routes.elicitacion_router import router as elicitacion_router
from app.routes.rf_router import router as rf_router
from app.routes.rnf_router import router as rnf_router
from app.routes.negociacion_router import router as negociacion_router
from app.routes.srs_router import router as srs_router

settings = get_settings()

# Crear tablas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SRS Manager API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(router)
app.include_router(proyecto_router)
app.include_router(stakeholder_router)
app.include_router(elicitacion_router)
app.include_router(rf_router)
app.include_router(rnf_router)
app.include_router(negociacion_router)
app.include_router(srs_router)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )

    schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/api/auth/token",
                    "scopes": {}
                }
            }
        }
    }

    for path in schema.get("paths", {}).values():
        for operation in path.values():
            if isinstance(operation, dict) and "security" in operation:
                operation["security"] = [{"OAuth2PasswordBearer": []}]

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/")
async def root():
    return {
        "message": "API en funcionamiento",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=settings.debug)