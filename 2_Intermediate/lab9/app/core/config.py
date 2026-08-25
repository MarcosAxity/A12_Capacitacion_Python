import os


class Settings:
    """Configuración centralizada. En un proyecto real vendría de variables
    de entorno (.env) usando pydantic-settings."""

    PROJECT_NAME: str = "Lab API"
    API_V1_PREFIX: str = "/api/v1"

    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-lab-key-change-me")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )

    # Orígenes permitidos para CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost", "http://localhost:3000"]


settings = Settings()
