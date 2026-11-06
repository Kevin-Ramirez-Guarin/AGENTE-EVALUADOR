"""Notificador inyectable: Google real, deshabilitado (sin token) o falso (pruebas)."""
from datetime import datetime

from app import google_apis


class NotificadorGoogle:
    habilitado = True

    def enviar_correo(self, destinatario: str, asunto: str, cuerpo: str) -> None:
        google_apis.enviar_correo(destinatario, asunto, cuerpo)

    def crear_entrevista(self, email: str, titulo: str, descripcion: str, inicio: datetime) -> dict:
        return google_apis.crear_entrevista(email, titulo, descripcion, inicio)


class NotificadorDeshabilitado:
    """No envía nada; se usa cuando aún no se autorizó Google."""
    habilitado = False


class NotificadorFalso:
    habilitado = True

    def __init__(self) -> None:
        self.correos: list[tuple[str, str, str]] = []
        self.entrevistas: list[tuple[str, str, str, datetime]] = []

    def enviar_correo(self, destinatario: str, asunto: str, cuerpo: str) -> None:
        self.correos.append((destinatario, asunto, cuerpo))

    def crear_entrevista(self, email: str, titulo: str, descripcion: str, inicio: datetime) -> dict:
        self.entrevistas.append((email, titulo, descripcion, inicio))
        return {"inicio": inicio.isoformat(), "meet_link": "https://meet.google.com/fake-test",
                "event_id": "fake"}


def get_notificador():
    return NotificadorGoogle() if google_apis.TOKEN_PATH.exists() else NotificadorDeshabilitado()
