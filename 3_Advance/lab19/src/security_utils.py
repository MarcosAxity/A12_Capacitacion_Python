"""
security_utils.py
==================

Utilidades reutilizables de "hardening" a nivel de aplicación:

- Redacción de datos sensibles en strings/diccionarios antes de loggear.
- Verificación básica de fortaleza de secretos (usada además de la
  validación de Pydantic en config.py).

Estas utilidades son intencionalmente simples y sin dependencias externas
para poder auditarlas fácilmente (menos código = menos superficie de
ataque).
"""

from __future__ import annotations

import re

# Claves cuyo valor jamás debe aparecer en texto plano en logs.
_SENSITIVE_KEYS = {
    "password",
    "secret",
    "secret_key",
    "api_key",
    "token",
    "database_url",
    "authorization",
}

_MASK = "**********"


def redact_dict(data: dict) -> dict:
    """Devuelve una copia de `data` con los valores de claves sensibles
    reemplazados por una máscara. No muta el diccionario original.
    """
    redacted = {}
    for key, value in data.items():
        if key.lower() in _SENSITIVE_KEYS:
            redacted[key] = _MASK if value else None
        elif isinstance(value, dict):
            redacted[key] = redact_dict(value)
        else:
            redacted[key] = value
    return redacted


_SECRET_LIKE_PATTERN = re.compile(
    r"(?i)(secret|token|api[_-]?key|password)\s*[:=]\s*([^\s,;]+)"
)


def redact_text(text: str) -> str:
    """Enmascara pares tipo `secret_key=valor` dentro de un texto libre
    (por ejemplo, un mensaje de excepción que podría incluir el valor de
    una variable de entorno concatenada por error).
    """
    return _SECRET_LIKE_PATTERN.sub(lambda m: f"{m.group(1)}={_MASK}", text)


def is_strong_secret(value: str, *, min_length: int = 16) -> bool:
    """Chequeo mínimo de fortaleza: longitud y variedad de caracteres.

    No pretende sustituir un generador criptográfico (usar `secrets.
    token_urlsafe`), solo sirve como guarda adicional (defense in depth)
    para detectar secretos triviales tipo "12345" o "changeme".
    """
    if len(value) < min_length:
        return False
    has_letter = any(c.isalpha() for c in value)
    has_digit = any(c.isdigit() for c in value)
    trivial_values = {"changeme", "password", "secret", "12345678", "admin"}
    if value.lower() in trivial_values:
        return False
    return has_letter and has_digit
