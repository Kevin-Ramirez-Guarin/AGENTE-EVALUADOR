"""Gmail + Calendar con OAuth de usuario (app de escritorio).

`credentials.json` lo descarga el usuario; `token.json` lo crea `scripts/autorizar_google.py`.
"""
import base64
import uuid
from datetime import datetime, timedelta
from email.message import EmailMessage
from pathlib import Path
from zoneinfo import ZoneInfo

BACKEND_DIR = Path(__file__).resolve().parent.parent
CREDENTIALS_PATH = BACKEND_DIR / "credentials.json"
TOKEN_PATH = BACKEND_DIR / "token.json"
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.events",
]
TZ_NAME = "America/Bogota"
TZ = ZoneInfo(TZ_NAME)
HORA_ENTREVISTA = 10
DURACION_MIN = 45


def _servicio(nombre: str, version: str):
    # Imports tardíos: la app arranca sin credenciales y las pruebas no tocan Google.
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds.valid and creds.refresh_token:
        creds.refresh(Request())
    return build(nombre, version, credentials=creds, cache_discovery=False)


def enviar_correo(destinatario: str, asunto: str, cuerpo_texto: str) -> None:
    msg = EmailMessage()
    msg["To"] = destinatario
    msg["Subject"] = asunto
    msg.set_content(cuerpo_texto)
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    _servicio("gmail", "v1").users().messages().send(userId="me", body={"raw": raw}).execute()


def crear_entrevista(email_candidato: str, titulo: str, descripcion: str,
                     inicio: datetime) -> dict:
    fin = inicio + timedelta(minutes=DURACION_MIN)
    evento = {
        "summary": titulo,
        "description": descripcion,
        "start": {"dateTime": inicio.isoformat(), "timeZone": TZ_NAME},
        "end": {"dateTime": fin.isoformat(), "timeZone": TZ_NAME},
        "attendees": [{"email": email_candidato}],
        "conferenceData": {"createRequest": {
            "requestId": str(uuid.uuid4()),
            "conferenceSolutionKey": {"type": "hangoutsMeet"}}},
    }
    creado = _servicio("calendar", "v3").events().insert(
        calendarId="primary", body=evento, conferenceDataVersion=1, sendUpdates="all"
    ).execute()
    return {"inicio": inicio.isoformat(), "meet_link": creado.get("hangoutLink"),
            "event_id": creado["id"]}


def siguiente_horario(ahora: datetime) -> datetime:
    """Siguiente día hábil a las 10:00 de Bogotá (sin festivos: deuda conocida)."""
    dia = ahora.astimezone(TZ).date() + timedelta(days=1)
    while dia.weekday() >= 5:  # sábado=5, domingo=6
        dia += timedelta(days=1)
    return datetime(dia.year, dia.month, dia.day, HORA_ENTREVISTA, tzinfo=TZ)
