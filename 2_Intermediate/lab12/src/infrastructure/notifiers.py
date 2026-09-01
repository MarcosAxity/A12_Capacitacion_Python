"""Adaptadores del puerto `Notifier`.

ISP: cada adaptador solo implementa `send(to, message)`, el único
método del puerto. Nadie está obligado a implementar métodos de
email, SMS o push que no le apliquen: cada canal es una clase
pequeña, independiente y sustituible.
"""


class ConsoleNotifier:
    """Adaptador simple usado en demos y tests: imprime en consola."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    def send(self, to: str, message: str) -> None:
        self.sent.append((to, message))
        print(f"[console] Para {to}: {message}")


class EmailNotifier:
    def __init__(self, smtp_host: str = "localhost") -> None:
        self.smtp_host = smtp_host
        self.sent: list[tuple[str, str]] = []

    def send(self, to: str, message: str) -> None:
        # Simulado: en un caso real aquí se usaría smtplib.
        self.sent.append((to, message))
        print(f"[email vía {self.smtp_host}] Para {to}: {message}")


class SmsNotifier:
    def __init__(self, gateway: str = "twilio-sim") -> None:
        self.gateway = gateway
        self.sent: list[tuple[str, str]] = []

    def send(self, to: str, message: str) -> None:
        self.sent.append((to, message))
        print(f"[sms vía {self.gateway}] Para {to}: {message}")
