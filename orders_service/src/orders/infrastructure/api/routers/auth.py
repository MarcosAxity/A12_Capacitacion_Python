"""Router de autenticación: emite JWT vía flujo OAuth2 Password."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from orders.infrastructure.api.schemas import TokenResponse
from orders.infrastructure.api.security import authenticate_user, create_access_token
from orders.infrastructure.config import Settings, get_settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    """Autentica y devuelve un access token JWT.

    Usuario de demostración: `demo` / `demo1234`.
    """
    user = authenticate_user(form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(subject=user.username, settings=settings)
    return TokenResponse(access_token=token)
