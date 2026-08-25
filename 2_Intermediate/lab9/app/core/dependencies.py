from app.core.security import decode_access_token
from app.db.fake_db import fake_users_db
from app.schemas.user import UserOut
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# tokenUrl apunta al endpoint que emite el token (se ve reflejado en OpenAPI)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserOut:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    username: str | None = payload.get("sub")
    if username is None or username not in fake_users_db:
        raise credentials_exception

    return UserOut(**fake_users_db[username])


async def get_current_active_user(
    current_user: UserOut = Depends(get_current_user),
) -> UserOut:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user
