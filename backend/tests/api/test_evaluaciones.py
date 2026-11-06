from sqlmodel import Session, select

from app.db import Auditoria, Evaluacion
from app.evaluador import evaluador_falso
from app.main import _cargar_vacantes
from tests.api.conftest import PDF, postular


def _otra_vacante(client):
    return next(v["id"] for v in client.get("/vacantes").json() if v["id"] != "backend-jr")


def _sugerido(client):
    return client.get("/evaluaciones/1").json()["resultado"]["veredicto_sugerido"]


def _otro(v):
    return "NO_CONTINUA" if v != "NO_CONTINUA" else "ENTREVISTA"


def test_evaluador_falso_es_determinista_y_valido():
    v = _cargar_vacantes()[0]
    a = evaluador_falso(PDF, v)
    assert a == evaluador_falso(PDF, v)
    assert 0 <= a[1].puntaje_total <= 100


def test_listar_vacio(client):
    r = client.get("/evaluaciones")
    assert r.status_code == 200 and r.json() == []


def test_listar_forma_y_ranking(client):
    postular(client, pdf=PDF + b"a")
    postular(client, pdf=PDF + b"zzzzzz")
    postular(client, pdf=PDF + b"mm")
    datos = client.get("/evaluaciones").json()
    puntajes = [d["puntaje_total"] for d in datos]
    assert len(datos) == 3 and puntajes == sorted(puntajes, reverse=True)
    assert len(set(puntajes)) > 1
    assert set(datos[0]) == {"id", "vacante_id", "candidato", "puntaje_total",
                             "veredicto_sugerido", "veredicto_final", "estado"}
    assert datos[0]["candidato"] == "Ana Pérez" and datos[0]["veredicto_final"] is None


def test_filtros_vacante_y_estado(client):
    postular(client, vacante_id="backend-jr")
    postular(client, vacante_id=_otra_vacante(client))
    assert len(client.get("/evaluaciones", params={"vacante_id": "backend-jr"}).json()) == 1
    assert client.get("/evaluaciones", params={"estado": "decidida"}).json() == []
    assert len(client.get("/evaluaciones", params={"estado": "pendiente_revision"}).json()) == 2


def test_detalle(client):
    postular(client)
    r = client.get("/evaluaciones/1")
    assert r.status_code == 200
    d = r.json()
    assert set(d) == {"id", "vacante_id", "candidato", "perfil", "resultado",
                      "veredicto_final", "estado"}
    assert "puntaje_total" in d["resultado"] and "resumen" in d["perfil"]
    assert "email" not in str(d)


def test_detalle_404(client):
    assert client.get("/evaluaciones/99").status_code == 404


def test_decision_aprueba_sugerido_sin_motivo(client, engine):
    postular(client)
    s = _sugerido(client)
    r = client.post("/evaluaciones/1/decision", json={"veredicto": s, "reclutador": "jvarz12"})
    assert r.status_code == 200
    assert r.json() == {"id": 1, "veredicto_final": s, "estado": "decidida", "entrevista": None}
    with Session(engine) as ses:
        ev = ses.get(Evaluacion, 1)
        assert ev.decidido_por == "jvarz12" and ev.estado == "decidida"
    assert client.get("/evaluaciones/1").json()["veredicto_final"] == s


def test_decision_distinta_requiere_motivo_422(client):
    postular(client)
    r = client.post("/evaluaciones/1/decision",
                    json={"veredicto": _otro(_sugerido(client)), "reclutador": "x"})
    assert r.status_code == 422
    assert client.get("/evaluaciones/1").json()["estado"] == "pendiente_revision"


def test_decision_distinta_con_motivo_queda_en_auditoria(client, engine):
    postular(client)
    nuevo = _otro(_sugerido(client))
    r = client.post("/evaluaciones/1/decision",
                    json={"veredicto": nuevo, "motivo": "Referido interno", "reclutador": "x"})
    assert r.status_code == 200
    with Session(engine) as s:
        a = s.exec(select(Auditoria).where(Auditoria.evento == "decision")).one()
        assert "Referido interno" in a.detalle and nuevo in a.detalle and "x" in a.detalle
        assert s.get(Evaluacion, 1).motivo == "Referido interno"


def test_decision_ya_decidida_409(client):
    postular(client)
    body = {"veredicto": _sugerido(client), "reclutador": "x"}
    client.post("/evaluaciones/1/decision", json=body)
    assert client.post("/evaluaciones/1/decision", json=body).status_code == 409


def test_decision_404(client):
    r = client.post("/evaluaciones/9/decision", json={"veredicto": "ENTREVISTA", "reclutador": "x"})
    assert r.status_code == 404


def test_decision_veredicto_invalido_422(client):
    postular(client)
    r = client.post("/evaluaciones/1/decision", json={"veredicto": "TAL_VEZ", "reclutador": "x"})
    assert r.status_code == 422


def test_cors_localhost_5173(client):
    r = client.options("/evaluaciones", headers={"Origin": "http://localhost:5173",
                                                 "Access-Control-Request-Method": "GET"})
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"
