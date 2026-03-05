# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.user import (
    UserRegister, UserLogin, TokenResponse,
    AuthResponse, UserResponse, RefreshTokenRequest
)
from app.services.auth import AuthService
from app.core.security import verify_token
from app.core.dependencies import get_current_user
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# ── /token — acepta form-data, exclusivo para Swagger UI ─────────────────────
@router.post("/token", response_model=TokenResponse, summary="Login para Swagger UI (form-data)")
async def login_swagger(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    login_data = UserLogin(username=form_data.username, password=form_data.password)
    try:
        user = AuthService.login_user(db, login_data)
        return AuthService.get_tokens(user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── /register — usado por Angular ─────────────────────────────────────────────
@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    try:
        user = AuthService.register_user(db, user_data)
        tokens = AuthService.get_tokens(user.id)
        return AuthResponse(
            user=UserResponse.model_validate(user),
            tokens=tokens,
            message="Usuario registrado exitosamente"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al registrar")


# ── /login — usado por Angular (JSON) ─────────────────────────────────────────
@router.post("/login", response_model=AuthResponse)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    try:
        user = AuthService.login_user(db, login_data)
        tokens = AuthService.get_tokens(user.id)
        return AuthResponse(
            user=UserResponse.model_validate(user),
            tokens=tokens,
            message="Sesion iniciada exitosamente"
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error(f"Error en login: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al iniciar sesion")


# ── /refresh ───────────────────────────────────────────────────────────────────
@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    payload = verify_token(request.refresh_token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token invalido")
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido")
    try:
        user_id = int(payload.get("sub"))
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido")
    user = AuthService.get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")
    return AuthService.get_tokens(user_id)


# ── /me ────────────────────────────────────────────────────────────────────────
@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


# ── /logout ────────────────────────────────────────────────────────────────────
@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Sesion cerrada exitosamente"}