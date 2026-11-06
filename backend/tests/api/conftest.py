import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app import db
from app.db import get_session
from app.evaluador import evaluador_falso, get_evaluador
from app.main import app
from app.notificador import NotificadorDeshabilitado, get_notificador
from app.routes import get_uploads_dir

PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\n%%EOF"


def evaluador_falso_kw(pdf, vacante, **kwargs):
    """Falso que acepta `identidad=` (lo agrega el track IA) sin depender del orden de fusión."""
    return evaluador_falso(pdf, vacante)


@pytest.fixture(autouse=True)
def _evaluador_falso_por_defecto(monkeypatch):
    """get_evaluador es el real por defecto; la API se prueba sin Gemini salvo que el test lo sobrescriba."""
    monkeypatch.setenv("EVALUADOR", "falso")


@pytest.fixture(autouse=True)
def _pdf_con_texto_por_defecto(monkeypatch):
    """Los PDF mínimos de las pruebas no tienen texto; la validación síncrona se prueba aparte."""
    monkeypatch.setattr("app.routes.extraer_texto_pdf", lambda _b: "texto", raising=False)


@pytest.fixture
def engine(tmp_path, monkeypatch):
    eng = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False}
    )
    SQLModel.metadata.create_all(eng)
    monkeypatch.setattr(db, "_engine", eng)  # la tarea en segundo plano abre su propia sesión
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
    app.dependency_overrides[get_evaluador] = lambda: evaluador_falso_kw
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
