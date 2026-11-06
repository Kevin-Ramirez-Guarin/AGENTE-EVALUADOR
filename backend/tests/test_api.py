from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_lista_vacantes():
    r = client.get("/vacantes")
    assert r.status_code == 200
    assert len(r.json()) == 5


def test_vacante_por_id():
    r = client.get("/vacantes/backend-jr")
    assert r.status_code == 200
    assert r.json()["id"] == "backend-jr"


def test_vacante_inexistente_404():
    assert client.get("/vacantes/no-existe").status_code == 404
