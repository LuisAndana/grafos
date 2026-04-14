from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.historial_schema import HistorialCreate, HistorialResponse
from app.services import historial_service as crud

router = APIRouter(prefix="/api/historial", tags=["Historial"])


@router.get("/", response_model=list[HistorialResponse])
def listar_historial(
    proyecto_id: int = Query(..., description="ID del proyecto"),
    db: Session = Depends(get_db),
):
    return crud.get_historial(db, proyecto_id)


@router.post("/", response_model=HistorialResponse, status_code=status.HTTP_201_CREATED)
def registrar_entrada(
    data: HistorialCreate,
    db: Session = Depends(get_db),
):
    return crud.create_entrada(db, data)


@router.delete("/")
def limpiar_historial(
    proyecto_id: int = Query(..., description="ID del proyecto"),
    db: Session = Depends(get_db),
):
    return crud.delete_historial(db, proyecto_id)


@router.post("/snapshot/{proyecto_id}", response_model=HistorialResponse, status_code=status.HTTP_201_CREATED)
def crear_snapshot(
    proyecto_id: int,
    db: Session = Depends(get_db),
):
    return crud.create_snapshot(db, proyecto_id)
