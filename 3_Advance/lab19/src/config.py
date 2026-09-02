"""
config.py
=========

Gestión centralizada de configuración y secretos usando `pydantic-settings`.

Principios de "Gestión de secretos y configuración" aplicados aquí:

1. Los secretos NUNCA se hardcodean en el código fuente.
2. Los secretos se cargan desde variables de entorno o un archivo `.env`
   (que está en `.gitignore` y NUNCA se sube al repositorio).
3. Los campos sensibles usan `SecretStr` de Pydantic: al hacer `print()`,
   `repr()` o loggear el objeto, el valor real queda oculto
   (se muestra como `**********`), reduciendo el riesgo de fuga accidental
   en logs, tracebacks o `print` de debug.
4. Se valida la configuración al arrancar la aplicación ("fail fast"): si
   falta un secreto obligatorio o tiene un formato inválido, la app no
   levanta, en lugar de fallar silenciosamente más tarde en producción.
5. Se distingue configuración por entorno (`development`, `staging`,
   `production`) para poder aplicar reglas más estrictas en producción
   (por ejemplo, prohibir `debug=True`).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la aplicación cargada desde entorno / `.env`.

    El orden de precedencia (de mayor a menor prioridad) que aplica
    pydantic-settings es:

        1. Variables de entorno del sistema (las que exporta el shell o
           el orquestador: Docker, Kubernetes, CI/CD, etc.)
        2. Archivo `.env` (solo para desarrollo local).
        3. Valores por defecto definidos en esta clase.

    Esto permite que en producción el valor real venga siempre de un
    gestor de secretos (Vault, AWS Secrets Manager, Docker secrets, CI
    secrets, etc.) inyectado como variable de entorno, sin tocar el
    código ni el `.env`.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        case_sensitive=False,
        extra="ignore",           # ignora variables de entorno no declaradas
        secrets_dir=None,         # se puede apuntar a /run/secrets en Docker Swarm
        validate_default=True,
    )

    # --- Metadatos de la app -------------------------------------------------
    app_name: str = Field(default="modulo19-seguridad", description="Nombre del servicio")
    environment: Literal["development", "staging", "production"] = Field(
        default="development", description="Entorno de ejecución"
    )
    debug: bool = Field(default=False, description="Activa logs/detalle extra")

    # --- Secretos --------------------------------------------------------------
    # SecretStr evita que el valor aparezca en logs, tracebacks o repr().
    secret_key: SecretStr = Field(
        ..., description="Clave usada para firmar tokens/sessiones (obligatoria)"
    )
    database_url: SecretStr = Field(
        ..., description="Cadena de conexión a la base de datos (obligatoria)"
    )
    api_key: SecretStr | None = Field(
        default=None, description="API key de un proveedor externo (opcional)"
    )

    # --- Parámetros de infraestructura -----------------------------------------
    request_timeout_seconds: float = Field(default=5.0, gt=0, le=60)
    max_retries: int = Field(default=3, ge=0, le=10)

    # --- Validaciones ------------------------------------------------------------
    @field_validator("secret_key")
    @classmethod
    def secret_key_min_length(cls, v: SecretStr) -> SecretStr:
        if len(v.get_secret_value()) < 16:
            raise ValueError(
                "secret_key debe tener al menos 16 caracteres. "
                "Genera uno seguro con: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        return v

    @field_validator("database_url")
    @classmethod
    def database_url_not_empty(cls, v: SecretStr) -> SecretStr:
        if not v.get_secret_value().strip():
            raise ValueError("database_url no puede estar vacío")
        return v

    def model_post_init(self, __context: object) -> None:
        # Regla de hardening: en producción, debug SIEMPRE debe estar apagado,
        # porque el modo debug puede filtrar tracebacks con datos sensibles.
        if self.environment == "production" and self.debug:
            raise ValueError(
                "Configuración insegura: 'debug' no puede ser True cuando "
                "environment='production'."
            )

    def safe_dict(self) -> dict:
        """Devuelve la configuración como dict apto para loggear.

        Los `SecretStr` se serializan enmascarados, nunca en texto plano.
        Útil para imprimir la config al arrancar la app sin filtrar secretos.
        """
        data = self.model_dump()
        for key, value in list(data.items()):
            if isinstance(getattr(self, key, None), SecretStr):
                data[key] = "**********" if value else None
        return data


@lru_cache
def get_settings() -> Settings:
    """Devuelve una instancia cacheada (singleton) de Settings.

    Se usa `lru_cache` para no releer/parsear el entorno en cada llamada,
    y para poder sobreescribir fácilmente en tests con
    `get_settings.cache_clear()` + variables de entorno de prueba.
    """
    return Settings()  # type: ignore[call-arg]
