import json

from sqlmodel import Session, select

from app.agent import PdfInvalidoError, PdfSinTextoError
from app.db import Auditoria, Evaluacion, Postulacion
from app.evaluador import get_evaluador
from app.main import app
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
