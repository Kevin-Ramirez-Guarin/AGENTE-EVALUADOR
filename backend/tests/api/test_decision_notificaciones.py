import json

import pytest
from sqlmodel import Session, select

from app.db import Auditoria, Evaluacion
from app.main import app
from app.notificador import NotificadorDeshabilitado, NotificadorFalso, get_notificador
from tests.api.conftest import postular


def _preparar(client, engine, veredicto_ia, criterios=None):
    postular(client)
    with Session(engine) as s:
        ev = s.get(Evaluacion, 1)
        res = dict(ev.resultado)
        res["veredicto_sugerido"] = veredicto_ia
        res["explicacion"] = "Explicación general."
        if criterios is not None:
            res["criterios"] = criterios
        ev.resultado, ev.veredicto_ia = res, veredicto_ia
        s.add(ev)
        s.commit()


def _eventos(engine):
    with Session(engine) as s:
        return [a.evento for a in s.exec(select(Auditoria).order_by(Auditoria.id)).all()]


def _decidir(client, veredicto):
    return client.post("/evaluaciones/1/decision",
                       json={"veredicto": veredicto, "reclutador": "jv"})


@pytest.fixture
def falso():
    n = NotificadorFalso()
    app.dependency_overrides[get_notificador] = lambda: n
    return n


def test_entrevista_agenda_y_envia_correo(client, engine, falso):
    _preparar(client, engine, "ENTREVISTA")
    r = _decidir(client, "ENTREVISTA")
    assert r.status_code == 200
    ent = r.json()["entrevista"]
    assert set(ent) == {"inicio", "meet_link"} and ent["meet_link"] in falso.correos[0][2]
    assert falso.correos[0][0] == "ana@example.com" and "Ana Pérez" in falso.correos[0][2]
    assert _eventos(engine)[-1] == "notificacion_enviada"


def _crit(criterio, nota, faltantes=("x",), puntaje=73.4):
    return {"criterio": criterio, "puntaje": puntaje, "peso": 0.3, "cumplidos": [],
            "faltantes": list(faltantes), "evidencias": [], "nota": nota}


def test_no_continua_usa_notas_de_criterios_con_faltantes_sin_cifras(client, engine, falso):
    crit = [_crit("experiencia", "Falta experiencia en APIs, quedó en 73.4% de lo pedido."),
            _crit("idiomas", "Esta nota no aplica.", faltantes=[]),
            _crit("educacion", "")]
    _preparar(client, engine, "NO_CONTINUA", crit)
    r = _decidir(client, "NO_CONTINUA")
    assert r.json()["entrevista"] is None and falso.entrevistas == []
    _, _, cuerpo = falso.correos[0]
    assert "Falta experiencia en APIs" in cuerpo and "una persona" in cuerpo
    assert "73.4" not in cuerpo and "%" not in cuerpo and "73" not in cuerpo
    assert "no aplica" not in cuerpo and "Explicación general." not in cuerpo


def test_no_continua_sin_notas_usa_texto_por_defecto(client, engine, falso):
    _preparar(client, engine, "NO_CONTINUA", [_crit("experiencia", "")])
    _decidir(client, "NO_CONTINUA")
    cuerpo = falso.correos[0][2]
    assert "no se ajustó a los requisitos" in cuerpo
    assert not any(l.strip() == "-" for l in cuerpo.splitlines())
    assert "Explicación general." not in cuerpo


def test_si_el_reclutador_contradice_a_la_ia_se_usa_su_motivo(client, engine, falso):
    _preparar(client, engine, "ENTREVISTA", [_crit("experiencia", "Nota interna de la IA.")])
    r = client.post("/evaluaciones/1/decision", json={
        "veredicto": "NO_CONTINUA", "motivo": "Buscamos más experiencia en SQL",
        "reclutador": "jv"})
    assert r.status_code == 200
    cuerpo = falso.correos[0][2]
    assert "Buscamos más experiencia en SQL" in cuerpo and "Nota interna" not in cuerpo


def test_revision_humana_no_envia_nada(client, engine, falso):
    _preparar(client, engine, "REVISION_HUMANA")
    assert _decidir(client, "REVISION_HUMANA").status_code == 200
    assert falso.correos == [] and falso.entrevistas == []
    assert _eventos(engine) == ["evaluacion_creada", "decision"]


def test_deshabilitado_audita_omitida_y_entrevista_null(client, engine):
    app.dependency_overrides[get_notificador] = lambda: NotificadorDeshabilitado()
    _preparar(client, engine, "ENTREVISTA")
    r = _decidir(client, "ENTREVISTA")
    assert r.status_code == 200 and r.json()["entrevista"] is None
    assert _eventos(engine)[-1] == "notificacion_omitida"


class _Roto(NotificadorFalso):
    def crear_entrevista(self, *a, **k):
        raise RuntimeError("Google caído")

    def enviar_correo(self, *a, **k):
        raise RuntimeError("Google caído")


class _RotoSoloCorreo(NotificadorFalso):
    def enviar_correo(self, *a, **k):
        raise RuntimeError("Gmail caído")


class _SinMeet(NotificadorFalso):
    def crear_entrevista(self, email, titulo, descripcion, inicio):
        return {"inicio": inicio.isoformat(), "meet_link": None, "event_id": "ev9"}


def test_evento_creado_y_correo_falla_devuelve_la_entrevista(client, engine):
    app.dependency_overrides[get_notificador] = lambda: _RotoSoloCorreo()
    _preparar(client, engine, "ENTREVISTA")
    r = _decidir(client, "ENTREVISTA")
    assert r.status_code == 200
    assert r.json()["entrevista"]["meet_link"] == "https://meet.google.com/fake-test"
    with Session(engine) as s:
        ultima = s.exec(select(Auditoria).order_by(Auditoria.id.desc())).first()
    d = json.loads(ultima.detalle)
    assert ultima.evento == "notificacion_fallida"
    assert d["event_id"] == "fake" and d["paso"] == "correo"


def test_sin_link_de_meet_es_fallo_parcial_y_no_envia_none(client, engine):
    n = _SinMeet()
    app.dependency_overrides[get_notificador] = lambda: n
    _preparar(client, engine, "ENTREVISTA")
    r = _decidir(client, "ENTREVISTA")
    assert r.status_code == 200 and n.correos == []
    with Session(engine) as s:
        ultima = s.exec(select(Auditoria).order_by(Auditoria.id.desc())).first()
    d = json.loads(ultima.detalle)
    assert ultima.evento == "notificacion_fallida" and d["paso"] == "meet" and d["event_id"] == "ev9"


@pytest.mark.parametrize("veredicto", ["ENTREVISTA", "NO_CONTINUA"])
def test_fallo_de_google_no_revierte_la_decision(client, engine, veredicto):
    app.dependency_overrides[get_notificador] = lambda: _Roto()
    _preparar(client, engine, veredicto)
    r = _decidir(client, veredicto)
    assert r.status_code == 200 and r.json()["entrevista"] is None
    with Session(engine) as s:
        assert s.get(Evaluacion, 1).estado == "decidida"
        ultima = s.exec(select(Auditoria).order_by(Auditoria.id.desc())).first()
    assert ultima.evento == "notificacion_fallida"
    assert json.loads(ultima.detalle)["error"] == "RuntimeError"
