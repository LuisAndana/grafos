from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
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
from app.models.requerimiento_funcional import RequerimientoFuncional

# Routers
from app.routes.auth import router
from app.routes.proyecto_router import router as proyecto_router
from app.routes.stakeholder_router import router as stakeholder_router
from app.routes.elicitacion_router import router as elicitacion_router
from app.routes.requerimiento_funcional_router import router as rf_router
from app.routes.generador_router import router as generador_router

settings = get_settings()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SRS Manager API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(proyecto_router)
app.include_router(stakeholder_router)
app.include_router(elicitacion_router)
app.include_router(rf_router)
app.include_router(generador_router)


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
            if "security" in operation:
                operation["security"] = [{"OAuth2PasswordBearer": []}]

    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi


@app.get("/")
async def root():
    return {"message": "API en funcionamiento", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=settings.debug)