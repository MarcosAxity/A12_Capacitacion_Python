"""Configuración de la aplicación vía variables de entorno (12-factor app)."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ORDERS_", env_file=".env", extra="ignore")

    database_url: str = Field(default="sqlite+aiosqlite:///./orders.db")
    jwt_secret_key: str = Field(default="change-me-in-production-please-use-32-bytes-min")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expire_minutes: int = Field(default=30)
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    sql_echo: bool = Field(default=False)

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
