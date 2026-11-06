import json
from datetime import datetime, timedelta, timezone

import pytest

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.agent import PdfInvalidoError, PdfSinTextoError
from app.db import Auditoria, Evaluacion, Postulacion
from app.evaluador import get_evaluador
from app.main import app
from app import routes
from tests.api.conftest import evaluador_falso_kw, postular


def _roto(pdf, vacante, **kwargs):
    raise RuntimeError("LLM caído con Ana Pérez ana@example.com")


def test_respuesta_201_es_en_evaluacion_y_luego_queda_pendiente(client):
    r = postular(client)
    assert r.status_code == 201
    assert r.json() == {"evaluacion_id": 1, "estado": "en_evaluacion"}
    d = client.get("/evaluaciones/1").json()
    assert d["estado"] == "pendiente_revision" and d["error"] is None
    assert d["resultado"]["puntaje_total"] >= 50


def test_evaluador_recibe_identidad_y_vacante(client):
    vistos = {}

    def _ev(pdf, vacante, **kwargs):
        vistos.update(kwargs, vacante=vacante.id)
        return evaluador_falso_kw(pdf, vacante)

    app.dependency_overrides[get_evaluador] = lambda: _ev
    postular(client)
    assert vistos == {"identidad": {"nombre": "Ana Pérez", "email": "ana@example.com"},
                      "vacante": "backend-jr"}


def test_evaluacion_creada_audita(client, engine):
    postular(client)
    with Session(engine) as s:
        assert [a.evento for a in s.exec(select(Auditoria))] == ["evaluacion_creada"]


def test_error_del_evaluador_deja_error_evaluacion_y_conserva_pdf(client, engine, uploads):
    app.dependency_overrides[get_evaluador] = lambda: _roto
    assert postular(client).status_code == 201
    d = client.get("/evaluaciones/1").json()
    assert d["estado"] == "error_evaluacion"
    assert d["perfil"] is None and d["resultado"] is None
    assert d["error"] and "Ana" not in d["error"] and "@" not in d["error"]
    with Session(engine) as s:
        a = s.exec(select(Auditoria)).one()
    assert a.evento == "evaluacion_fallida" and a.evaluacion_id == 1
    assert "Ana" not in a.detalle and json.loads(a.detalle)["error"] == "RuntimeError"
    assert len(list(uploads.iterdir())) == 1


def test_reintentar_error_funciona(client, engine):
    app.dependency_overrides[get_evaluador] = lambda: _roto
    postular(client)
    app.dependency_overrides[get_evaluador] = lambda: evaluador_falso_kw
    r = client.post("/evaluaciones/1/reintentar")
    assert r.status_code == 202
    d = client.get("/evaluaciones/1").json()
    assert d["estado"] == "pendiente_revision" and d["error"] is None
    with Session(engine) as s:
        assert [a.evento for a in s.exec(select(Auditoria))] == [
            "evaluacion_fallida", "evaluacion_creada"]


def test_reintentar_fuera_de_error_409_y_404(client):
    postular(client)
    assert client.post("/evaluaciones/1/reintentar").status_code == 409
    assert client.post("/evaluaciones/99/reintentar").status_code == 404


def _forzar_en_evaluacion(engine, ev_id):
    with Session(engine) as s:
        ev = s.get(Evaluacion, ev_id)
        ev.estado, ev.puntaje_total, ev.resultado, ev.perfil, ev.veredicto_ia = (
            "en_evaluacion", None, None, None, None)
        s.add(ev)
        s.commit()


def test_decision_sobre_en_evaluacion_409(client, engine):
    postular(client)
    _forzar_en_evaluacion(engine, 1)
    r = client.post("/evaluaciones/1/decision",
                    json={"veredicto": "ENTREVISTA", "motivo": "x", "reclutador": "r"})
    assert r.status_code == 409


def test_decision_sobre_error_evaluacion_409(client):
    app.dependency_overrides[get_evaluador] = lambda: _roto
    postular(client)
    r = client.post("/evaluaciones/1/decision",
                    json={"veredicto": "ENTREVISTA", "motivo": "x", "reclutador": "r"})
    assert r.status_code == 409


def test_orden_evaluadas_luego_en_evaluacion_luego_error(client, engine):
    postular(client, pdf=b"%PDF-1.4 a")
    postular(client, pdf=b"%PDF-1.4 zzzzzz")
    app.dependency_overrides[get_evaluador] = lambda: _roto
    postular(client)  # id 3 -> error
    _forzar_en_evaluacion(engine, 2)
    filas = client.get("/evaluaciones").json()
    assert [f["estado"] for f in filas] == ["pendiente_revision", "en_evaluacion", "error_evaluacion"]
    assert filas[1]["puntaje_total"] is None and filas[1]["veredicto_sugerido"] is None


def test_pdf_sin_texto_422_sincrono_sin_guardar(client, engine, uploads, monkeypatch):
    def _sin_texto(_b):
        raise PdfSinTextoError("escaneo")

    monkeypatch.setattr("app.routes.extraer_texto_pdf", _sin_texto)
    r = postular(client)
    assert r.status_code == 422 and "texto seleccionable" in r.json()["detail"]
    with Session(engine) as s:
        assert s.exec(select(Postulacion)).all() == []
        assert s.exec(select(Auditoria)).one().evento == "postulacion_rechazada"
    assert list(uploads.iterdir()) == []


def test_pdf_corrupto_415_sincrono(client, monkeypatch):
    def _corrupto(_b):
        raise PdfInvalidoError("corrupto")

    monkeypatch.setattr("app.routes.extraer_texto_pdf", _corrupto)
    assert postular(client).status_code == 415


def _fijar(engine, ev_id, **campos):
    with Session(engine) as s:
        ev = s.get(Evaluacion, ev_id)
        for k, v in campos.items():
            setattr(ev, k, v)
        s.add(ev)
        s.commit()


def _hace(minutos):
    return datetime.now(timezone.utc) - timedelta(minutes=minutos)


@pytest.fixture
def diferida(monkeypatch):
    """Intercepta la tarea: el POST deja la fila en_evaluacion hasta que la prueba la ejecute."""
    pendientes = []
    real = routes.evaluar_en_segundo_plano
    monkeypatch.setattr(routes, "evaluar_en_segundo_plano", lambda *a: pendientes.append(a))
    return pendientes, real


def test_estado_en_evaluacion_hasta_que_corre_la_tarea(client, engine, uploads, diferida):
    pendientes, tarea = diferida
    postular(client)
    d = client.get("/evaluaciones/1").json()
    assert d["estado"] == "en_evaluacion" and d["resultado"] is None
    assert len(pendientes) == 1
    with Session(engine) as s:
        assert s.get(Evaluacion, 1).evaluacion_iniciada_at is not None

    llamadas = []

    def _ev(pdf, vacante, **kwargs):
        llamadas.append(kwargs)
        return evaluador_falso_kw(pdf, vacante)

    tarea(1, _ev, uploads)
    assert client.get("/evaluaciones/1").json()["estado"] == "pendiente_revision"
    assert llamadas == [{"identidad": {"nombre": "Ana Pérez", "email": "ana@example.com"}}]


def test_doble_reintento_solo_programa_una_vez(client, engine, diferida):
    pendientes, _ = diferida
    postular(client)
    _fijar(engine, 1, estado="error_evaluacion", error="x")
    pendientes.clear()
    assert client.post("/evaluaciones/1/reintentar").status_code == 202
    assert client.post("/evaluaciones/1/reintentar").status_code == 409
    assert len(pendientes) == 1


def test_reintentar_en_evaluacion_atascada_si_pasaron_mas_de_10_min(client, engine, diferida):
    pendientes, _ = diferida
    postular(client)
    pendientes.clear()
    _fijar(engine, 1, evaluacion_iniciada_at=_hace(2))
    assert client.post("/evaluaciones/1/reintentar").status_code == 409
    _fijar(engine, 1, evaluacion_iniciada_at=_hace(11))
    assert client.post("/evaluaciones/1/reintentar").status_code == 202
    assert len(pendientes) == 1


def test_arranque_marca_interrumpidas_las_atascadas(client, engine, diferida):
    postular(client)
    postular(client)
    _fijar(engine, 1, evaluacion_iniciada_at=_hace(30))
    with TestClient(app):  # ejecuta el lifespan
        pass
    d1, d2 = client.get("/evaluaciones/1").json(), client.get("/evaluaciones/2").json()
    assert (d1["estado"], d1["error"]) == ("error_evaluacion", "interrumpida")
    assert d2["estado"] == "en_evaluacion"


def test_fallo_al_guardar_resultado_deja_error_evaluacion(client, engine, uploads, diferida,
                                                          monkeypatch):
    _, tarea = diferida
    postular(client)

    class SesionQueFalla(Session):
        usos = 0

        def commit(self):
            SesionQueFalla.usos += 1
            if SesionQueFalla.usos == 1:
                raise RuntimeError("BD caída")
            super().commit()

    monkeypatch.setattr(routes, "Session", SesionQueFalla)
    tarea(1, evaluador_falso_kw, uploads)
    d = client.get("/evaluaciones/1").json()
    assert d["estado"] == "error_evaluacion" and d["error"] and "Ana" not in d["error"]
