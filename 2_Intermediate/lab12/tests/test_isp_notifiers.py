"""Tests de los adaptadores del puerto `Notifier` (ISP).

Cada notifier implementa un único método (`send`). Esto permite
testear cada canal de forma totalmente independiente, sin necesitar
stubear métodos de otros canales que no le corresponden.
"""

from src.infrastructure.notifiers import ConsoleNotifier, EmailNotifier, SmsNotifier


def test_console_notifier_registra_el_envio():
    notifier = ConsoleNotifier()
    notifier.send("ana@example.com", "hola")
    assert notifier.sent == [("ana@example.com", "hola")]


def test_email_notifier_registra_el_envio():
    notifier = EmailNotifier(smtp_host="smtp.test.com")
    notifier.send("ana@example.com", "hola por email")
    assert notifier.sent == [("ana@example.com", "hola por email")]


def test_sms_notifier_registra_el_envio():
    notifier = SmsNotifier(gateway="gw-test")
    notifier.send("+525500000000", "hola por sms")
    assert notifier.sent == [("+525500000000", "hola por sms")]
