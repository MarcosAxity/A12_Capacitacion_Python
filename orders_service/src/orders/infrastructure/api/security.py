"""Seguridad: hashing de contraseñas y emisión/validación de JWT.

Se usa bcrypt==4.0.1 + passlib==1.7.4 (combinación estable, evita el
AttributeError conocido de bcrypt>=4.1.1 con passlib).

NOTA: el "store" de usuarios es en memoria y sirve solo para demostrar el
flujo de autenticación del laboratorio. En producción se reemplazaría por
un puerto UserRepository con su propio adaptador, igual que OrderRepository.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import BaseModel

from orders.infrastructure.config import Settings, get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


class TokenPayload(BaseModel):
    sub: str
    exp: int


class _FakeUser(BaseModel):
    username: str
    hashed_password: str


# Store de usuarios en memoria únicamente para fines demostrativos del lab.
_FAKE_USERS_DB: dict[str, _FakeUser] = {
    "demo": _FakeUser(
        username="demo",
        # password: "demo1234"
        hashed_password=pwd_context.hash("demo1234"),
    )
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(username: str, password: str) -> _FakeUser | None:
    user = _FAKE_USERS_DB.get(username)
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(subject: str, settings: Settings) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    settings: Settings = Depends(get_settings),
) -> str:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        username = payload.get("sub")
        if username is None:
            raise credentials_error
        return username
    except jwt.PyJWTError as exc:
        raise credentials_error from exc
