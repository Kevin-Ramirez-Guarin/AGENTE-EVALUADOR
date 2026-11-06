import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.db import get_session
from app.main import app
from app.notificador import NotificadorDeshabilitado, get_notificador
from app.routes import get_uploads_dir

PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\n%%EOF"


@pytest.fixture
def engine(tmp_path):
    eng = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False}
    )
    SQLModel.metadata.create_all(eng)
    return eng


@pytest.fixture
def uploads(tmp_path):
    d = tmp_path / "uploads"
    d.mkdir()
    return d


@pytest.fixture
def client(engine, uploads):
    def _session():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = _session
    app.dependency_overrides[get_uploads_dir] = lambda: uploads
    # Por defecto nunca se toca Google en las pruebas, aunque exista un token.json local.
    app.dependency_overrides[get_notificador] = lambda: NotificadorDeshabilitado()
    yield TestClient(app)
    app.dependency_overrides.clear()


def postular(client, *, vacante_id="backend-jr", consentimiento="true", pdf=PDF,
             filename="hv.pdf", content_type="application/pdf", nombre="Ana Pérez",
             email="ana@example.com"):
    return client.post(
        "/postulaciones",
        data={"vacante_id": vacante_id, "nombre": nombre, "email": email,
              "consentimiento": consentimiento},
        files={"pdf": (filename, pdf, content_type)},
    )
