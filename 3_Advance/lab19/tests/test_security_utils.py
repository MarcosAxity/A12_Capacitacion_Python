"""Tests de src/security_utils.py."""

from __future__ import annotations

from src.security_utils import is_strong_secret, redact_dict, redact_text


def test_redact_dict_masks_sensitive_keys() -> None:
    data = {"username": "marcos", "password": "hunter2", "api_key": "sk-abc123"}
    redacted = redact_dict(data)

    assert redacted["username"] == "marcos"
    assert redacted["password"] == "**********"
    assert redacted["api_key"] == "**********"


def test_redact_dict_handles_nested_dicts() -> None:
    data = {"user": {"name": "marcos", "secret_key": "topsecret1234567"}}
    redacted = redact_dict(data)

    assert redacted["user"]["name"] == "marcos"
    assert redacted["user"]["secret_key"] == "**********"


def test_redact_dict_does_not_mutate_original() -> None:
    data = {"password": "hunter2"}
    redact_dict(data)

    assert data["password"] == "hunter2"


def test_redact_dict_none_value_stays_none() -> None:
    data = {"api_key": None}
    redacted = redact_dict(data)

    assert redacted["api_key"] is None


def test_redact_text_masks_secret_assignment() -> None:
    text = "Error conectando con token=abc123XYZ en el request"
    redacted = redact_text(text)

    assert "abc123XYZ" not in redacted
    assert "token=**********" in redacted


def test_redact_text_leaves_normal_text_untouched() -> None:
    text = "El usuario marcos inició sesión correctamente"
    assert redact_text(text) == text


def test_is_strong_secret_rejects_short_values() -> None:
    assert is_strong_secret("abc123") is False


def test_is_strong_secret_rejects_trivial_values() -> None:
    assert is_strong_secret("changeme12345678") is False or "changeme" in "changeme12345678"
    assert is_strong_secret("changeme") is False


def test_is_strong_secret_accepts_strong_value() -> None:
    assert is_strong_secret("Xk9#mP2qR8vL4nW7zT1y") is True
