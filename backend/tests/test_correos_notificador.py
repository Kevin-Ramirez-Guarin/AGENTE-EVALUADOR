from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from app import google_apis, notificador
from app.correos import correo_invitacion, correo_no_continua
from app.notificador import NotificadorDeshabilitado, NotificadorFalso, NotificadorGoogle

INICIO = datetime(2026, 11, 9, 10, 0, tzinfo=ZoneInfo("America/Bogota"))


def test_invitacion_lleva_nombre_fecha_y_link():
    asunto, cuerpo = correo_invitacion("Ana Pérez", "Backend Jr", INICIO.isoformat(),
                                       "https://meet.google.com/abc")
    assert "Ana Pérez" in cuerpo and "Backend Jr" in (asunto + cuerpo)
    assert "https://meet.google.com/abc" in cuerpo and "09/11/2026" in cuerpo


def test_no_continua_explica_por_criterio_sin_puntaje_y_dice_que_decidio_una_persona():
    asunto, cuerpo = correo_no_continua(
        "Ana Pérez", "Backend Jr", ["Experiencia: falta experiencia con APIs."])
    assert "Ana Pérez" in cuerpo
    assert "Experiencia: falta experiencia con APIs." in cuerpo
    assert "una persona" in cuerpo and "revisión" in cuerpo
    assert "%" not in cuerpo and "puntaje" not in cuerpo.lower()


def test_falso_registra_llamadas():
    n = NotificadorFalso()
    n.enviar_correo("a@b.co", "As", "Cu")
    r = n.crear_entrevista("a@b.co", "T", "D", INICIO)
    assert n.correos == [("a@b.co", "As", "Cu")] and len(n.entrevistas) == 1
    assert r["meet_link"] and n.habilitado


def test_get_notificador_sin_token_esta_deshabilitado(tmp_path):
    with patch.object(google_apis, "TOKEN_PATH", tmp_path / "token.json"):
        n = notificador.get_notificador()
    assert isinstance(n, NotificadorDeshabilitado) and not n.habilitado


def test_get_notificador_con_token_usa_google(tmp_path):
    tok = tmp_path / "token.json"
    tok.write_text("{}")
    with patch.object(google_apis, "TOKEN_PATH", tok):
        assert isinstance(notificador.get_notificador(), NotificadorGoogle)


def test_google_delega_en_google_apis():
    with patch.object(google_apis, "enviar_correo") as env, \
            patch.object(google_apis, "crear_entrevista", return_value={"x": 1}) as cre:
        n = NotificadorGoogle()
        n.enviar_correo("a@b.co", "As", "Cu")
        assert n.crear_entrevista("a@b.co", "T", "D", INICIO) == {"x": 1}
    env.assert_called_once_with("a@b.co", "As", "Cu")
    cre.assert_called_once()
