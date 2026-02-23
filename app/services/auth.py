# -*- coding: utf-8 -*-
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from app.models.user import User
from app.schemas.user import UserRegister, UserLogin, TokenResponse
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, \
    get_token_expiration_time


class AuthService:

    @staticmethod
    def register_user(db: Session, user_data: UserRegister) -> User:
        try:
            existing_user = db.query(User).filter(
                (User.email == user_data.email) | (User.username == user_data.username)
            ).first()

            if existing_user:
                if existing_user.email == user_data.email:
                    raise ValueError("El email ya esta registrado")
                else:
                    raise ValueError("El nombre de usuario ya esta en uso")

            hashed_password = hash_password(user_data.password)
            db_user = User(
                email=user_data.email,
                username=user_data.username,
                hashed_password=hashed_password
            )

            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user

        except IntegrityError:
            db.rollback()
            raise ValueError("Error al registrar el usuario")

    @staticmethod
    def login_user(db: Session, login_data: UserLogin) -> User:
        user = db.query(User).filter(
            User.username == login_data.username
        ).first()

        if not user or not verify_password(login_data.password, user.hashed_password):
            raise ValueError("Nombre de usuario o contrasena incorrectos")

        if not user.is_active:
            raise ValueError("La cuenta esta desactivada")

        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def get_tokens(user_id: int) -> TokenResponse:
        access_token = create_access_token(
            data={"sub": str(user_id), "type": "access"}
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user_id), "type": "refresh"}
        )

        access_token_expiration = get_token_expiration_time(access_token)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=access_token_expiration or 900
        )

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User:
        return db.query(User).filter(User.id == user_id).first()
