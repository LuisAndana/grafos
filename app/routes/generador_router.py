from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.generador_schema import (
    GeneradorCodigoResponse,
    GeneradorDiagramaRequest,
    GeneradorDiagramaResponse,
)
from app.services import generador_service as service

router = APIRouter(prefix="/api/generador", tags=["Generador IA"])


@router.get("/test-conexion")
def test_conexion():
    """Prueba rápida: verifica token y conexión con GitHub Models."""
    return service.test_conexion()


@router.post("/codigo/{proyecto_id}", response_model=GeneradorCodigoResponse)
def generar_codigo(
    proyecto_id: int,
    db: Session = Depends(get_db),
):
    """Genera código Angular + FastAPI + SQL para el proyecto usando IA."""
    return service.generar_codigo(db, proyecto_id)


@router.post("/diagrama/{proyecto_id}", response_model=GeneradorDiagramaResponse)
def generar_diagrama(
    proyecto_id: int,
    body: GeneradorDiagramaRequest,
    db: Session = Depends(get_db),
):
    """Genera un diagrama Mermaid del tipo solicitado para el proyecto."""
    return service.generar_diagrama(db, proyecto_id, body.tipo)
