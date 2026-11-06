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


def test_no_continua_envia_explicacion_por_criterio(client, engine, falso):
    crit = [{"criterio": "experiencia", "puntaje": 12.0, "peso": 0.3, "cumplidos": [],
             "faltantes": [], "evidencias": [], "nota": "Falta experiencia en APIs."},
            {"criterio": "idiomas", "puntaje": 40.0, "peso": 0.1, "cumplidos": [],
             "faltantes": [], "evidencias": [], "nota": ""}]
    _preparar(client, engine, "NO_CONTINUA", crit)
    r = _decidir(client, "NO_CONTINUA")
    assert r.json()["entrevista"] is None and falso.entrevistas == []
    _, _, cuerpo = falso.correos[0]
    assert "Falta experiencia en APIs." in cuerpo and "una persona" in cuerpo
    assert "12" not in cuerpo and "Explicación general." not in cuerpo


def test_no_continua_sin_criterios_usa_explicacion(client, engine, falso):
    _preparar(client, engine, "NO_CONTINUA")
    _decidir(client, "NO_CONTINUA")
    assert "Explicación general." in falso.correos[0][2]


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
