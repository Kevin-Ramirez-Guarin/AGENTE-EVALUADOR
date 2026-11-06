"""Sin el stub del conftest: la validación síncrona corre con PDF reales de samples/."""
from pathlib import Path

import pytest

from app.agent import extraer_texto_pdf
from tests.api.conftest import postular

SAMPLES = Path(__file__).resolve().parents[3] / "samples"


@pytest.fixture(autouse=True)
def _validacion_real(monkeypatch):
    monkeypatch.setattr("app.routes.extraer_texto_pdf", extraer_texto_pdf)


def test_pdf_real_con_texto_201_y_se_evalua(client):
    r = postular(client, pdf=(SAMPLES / "hv_backend_fuerte_1.pdf").read_bytes())
    assert r.status_code == 201
    assert client.get(f"/evaluaciones/{r.json()['evaluacion_id']}").json()["estado"] == "pendiente_revision"


def test_pdf_real_escaneado_422_sin_guardar(client, uploads):
    r = postular(client, pdf=(SAMPLES / "hv_escaneada.pdf").read_bytes())
    assert r.status_code == 422 and "texto seleccionable" in r.json()["detail"]
    assert list(uploads.iterdir()) == []
    assert client.get("/evaluaciones").json() == []
