import base64
from datetime import datetime
from email import message_from_bytes
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

from app import google_apis

BOGOTA = ZoneInfo("America/Bogota")


def _en_bogota(*args):
    return datetime(*args, tzinfo=BOGOTA)


def test_siguiente_horario_viernes_a_lunes():
    r = google_apis.siguiente_horario(_en_bogota(2026, 11, 6, 15, 30))  # viernes
    assert r == _en_bogota(2026, 11, 9, 10, 0)


def test_siguiente_horario_sabado_a_lunes():
    r = google_apis.siguiente_horario(_en_bogota(2026, 11, 7, 9, 0))
    assert r == _en_bogota(2026, 11, 9, 10, 0)


def test_siguiente_horario_entre_semana_es_el_dia_siguiente():
    r = google_apis.siguiente_horario(_en_bogota(2026, 11, 3, 23, 0))  # martes
    assert r == _en_bogota(2026, 11, 4, 10, 0)


def test_siguiente_horario_conserva_zona_y_convierte_desde_utc():
    # viernes 23:30 en Bogota = sabado 04:30 UTC: sigue siendo viernes para Bogota.
    utc = datetime(2026, 11, 7, 4, 30, tzinfo=ZoneInfo("UTC"))
    r = google_apis.siguiente_horario(utc)
    assert r.tzinfo is not None and r.utcoffset().total_seconds() == -5 * 3600
    assert r == _en_bogota(2026, 11, 9, 10, 0)


def test_enviar_correo_codifica_mime_base64url():
    svc = MagicMock()
    with patch.object(google_apis, "_servicio", return_value=svc):
        google_apis.enviar_correo("ana@example.com", "Hola ñ", "Cuerpo con tildes: áé")
    cuerpo = svc.users().messages().send.call_args.kwargs
    assert cuerpo["userId"] == "me"
    raw = cuerpo["body"]["raw"]
    msg = message_from_bytes(base64.urlsafe_b64decode(raw))
    assert msg["To"] == "ana@example.com"
    assert "áé" in msg.get_payload(decode=True).decode("utf-8")


def test_crear_entrevista_arma_evento_con_meet():
    svc = MagicMock()
    svc.events().insert().execute.return_value = {
        "id": "ev1", "hangoutLink": "https://meet.google.com/abc-defg-hij"}
    inicio = _en_bogota(2026, 11, 9, 10, 0)
    with patch.object(google_apis, "_servicio", return_value=svc):
        r = google_apis.crear_entrevista("ana@example.com", "Entrevista", "Desc", inicio)
    kw = svc.events().insert.call_args.kwargs
    assert kw["conferenceDataVersion"] == 1 and kw["sendUpdates"] == "all"
    ev = kw["body"]
    assert ev["attendees"] == [{"email": "ana@example.com"}]
    assert ev["start"]["timeZone"] == "America/Bogota"
    assert ev["end"]["dateTime"] == "2026-11-09T10:45:00-05:00"
    assert ev["conferenceData"]["createRequest"]["requestId"]
    assert r == {"inicio": "2026-11-09T10:00:00-05:00",
                 "meet_link": "https://meet.google.com/abc-defg-hij", "event_id": "ev1"}
