from datetime import timedelta

from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.db.fake_db import fake_users_db
from app.schemas.token import Token
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=Token,
    summary="Obtener token de acceso (JWT)",
    description="Recibe usuario/contraseña (form-data OAuth2) y devuelve un token Bearer.",
)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    user = fake_users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=access_token)
