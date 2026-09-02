"""Tests de src/config.py.

Cubren:
- Carga correcta de settings desde variables de entorno.
- Falla ("fail fast") cuando faltan secretos obligatorios.
- Validación de longitud mínima de secret_key.
- Enmascarado de secretos en safe_dict().
- Regla de hardening: debug=True prohibido en production.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.config import Settings, get_settings


VALID_ENV = {
    "APP_SECRET_KEY": "una-clave-super-secreta-de-32+",
    "APP_DATABASE_URL": "postgresql://user:pass@localhost:5432/db",
}


def test_settings_load_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in VALID_ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("APP_APP_NAME", "mi-app")
    monkeypatch.setenv("APP_ENVIRONMENT", "development")

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.app_name == "mi-app"
    assert settings.environment == "development"
    assert settings.secret_key.get_secret_value() == VALID_ENV["APP_SECRET_KEY"]


def test_missing_required_secret_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("APP_SECRET_KEY", raising=False)
    monkeypatch.delenv("APP_DATABASE_URL", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_short_secret_key_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_SECRET_KEY", "corta")
    monkeypatch.setenv("APP_DATABASE_URL", VALID_ENV["APP_DATABASE_URL"])

    with pytest.raises(ValidationError, match="al menos 16 caracteres"):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_empty_database_url_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_SECRET_KEY", VALID_ENV["APP_SECRET_KEY"])
    monkeypatch.setenv("APP_DATABASE_URL", "   ")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_debug_true_forbidden_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in VALID_ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("APP_ENVIRONMENT", "production")
    monkeypatch.setenv("APP_DEBUG", "true")

    with pytest.raises(ValueError, match="Configuración insegura"):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_safe_dict_masks_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in VALID_ENV.items():
        monkeypatch.setenv(key, value)

    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    dumped = settings.safe_dict()

    assert dumped["secret_key"] == "**********"
    assert dumped["database_url"] == "**********"
    assert VALID_ENV["APP_SECRET_KEY"] not in str(dumped)


def test_secret_str_not_leaked_in_repr(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in VALID_ENV.items():
        monkeypatch.setenv(key, value)

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert VALID_ENV["APP_SECRET_KEY"] not in repr(settings.secret_key)
    assert VALID_ENV["APP_SECRET_KEY"] not in str(settings.secret_key)


def test_get_settings_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in VALID_ENV.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()

    s1 = get_settings()
    s2 = get_settings()

    assert s1 is s2  # misma instancia -> confirma el cacheo (lru_cache)
    get_settings.cache_clear()
