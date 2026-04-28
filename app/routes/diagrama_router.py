from fastapi import APIRouter, Depends, Query, Path, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.schemas.diagrama_schema import (
    DiagramaCreate, DiagramaUpdate, DiagramaResponse,
    DiagramaGuardarEstado, DiagramaListResponse
)
from app.services import diagrama_service as crud

router = APIRouter(prefix="/api/diagramas", tags=["Diagramas"])


@router.get("/proyecto/{proyecto_id}", response_model=DiagramaListResponse)
def listar_diagramas(
    proyecto_id: int = Path(..., description="ID del proyecto", gt=0),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo de diagrama"),
    db: Session = Depends(get_db),
):
    """
    Listar diagramas de un proyecto.

    Parámetros:
    - proyecto_id: ID del proyecto
    - tipo: Tipo de diagrama (opcional): class, sequence, package, usecase
    """
    if tipo:
        items = crud.get_diagramas_by_tipo(db, proyecto_id, tipo)
    else:
        items = crud.get_diagramas_by_proyecto(db, proyecto_id)

    return DiagramaListResponse(
        total=len(items),
        items=items
    )


@router.post("/", response_model=DiagramaResponse, status_code=status.HTTP_201_CREATED)
def crear_diagrama(
    data: DiagramaCreate,
    db: Session = Depends(get_db),
):
    """
    Crear nuevo diagrama para un proyecto.

    Tipos soportados:
    - class: Diagrama de clases UML
    - sequence: Diagrama de secuencia
    - package: Diagrama de paquetes
    - usecase: Diagrama de casos de uso
    """
    return crud.create_diagrama(db, data)


@router.get("/{diagrama_id}", response_model=DiagramaResponse)
def obtener_diagrama(
    diagrama_id: int,
    db: Session = Depends(get_db),
):
    """Obtener un diagrama específico por su ID."""
    return crud.get_diagrama(db, diagrama_id)


@router.put("/{diagrama_id}", response_model=DiagramaResponse)
def actualizar_diagrama(
    diagrama_id: int,
    data: DiagramaUpdate,
    db: Session = Depends(get_db),
):
    """Actualizar propiedades de un diagrama."""
    return crud.update_diagrama(db, diagrama_id, data)


@router.patch("/{diagrama_id}/guardar-estado", response_model=DiagramaResponse)
def guardar_estado_diagrama(
    diagrama_id: int,
    data: DiagramaGuardarEstado,
    db: Session = Depends(get_db),
):
    """
    Guardar el estado completo del diagrama (elementos, conexiones, vista).

    Este endpoint es usado por el editor para persistir cambios en tiempo real.
    """
    return crud.guardar_estado_diagrama(db, diagrama_id, data)


@router.delete("/{diagrama_id}")
def eliminar_diagrama(
    diagrama_id: int,
    db: Session = Depends(get_db),
):
    """Eliminar un diagrama."""
    return crud.delete_diagrama(db, diagrama_id)
