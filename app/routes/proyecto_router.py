# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.proyecto_schema import ProyectoCreate, ProyectoUpdate, ProyectoResponse
from app.services import proyecto_service as crud

router = APIRouter(prefix="/proyectos", tags=["Proyectos"])


# ─── RUTA DE DEBUG — quitar después de resolver el 403 ───────────────────────
@router.post("/debug", include_in_schema=False)
async def debug_token(request: Request):
    """Muestra exactamente qué Authorization header llega."""
    auth_header = request.headers.get("Authorization", "NO ENCONTRADO")
    return {
        "authorization_header": auth_header,
        "headers": dict(request.headers),
    }
# ─────────────────────────────────────────────────────────────────────────────


@router.post(
    "/",
    response_model=ProyectoResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_proyecto(
    data: ProyectoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.create_proyecto(db, data, user_id=current_user.id)


@router.get("/", response_model=list[ProyectoResponse])
def listar_proyectos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.get_proyectos(db, user_id=current_user.id)


@router.get("/{proyecto_id}", response_model=ProyectoResponse)
def obtener_proyecto(
    proyecto_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.get_proyecto(db, proyecto_id, user_id=current_user.id)


@router.put("/{proyecto_id}", response_model=ProyectoResponse)
def actualizar_proyecto(
    proyecto_id: int,
    data: ProyectoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.update_proyecto(db, proyecto_id, data, user_id=current_user.id)


@router.delete("/{proyecto_id}")
def eliminar_proyecto(
    proyecto_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.delete_proyecto(db, proyecto_id, user_id=current_user.id)