import json

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.db import Auditoria, Candidato, Evaluacion, Postulacion, get_session
from app.main import app
from app.routes import get_uploads_dir
from tests.api.conftest import PDF, postular

MB5 = 5 * 1024 * 1024


def test_crear_postulacion_201(client):
    r = postular(client)
    assert r.status_code == 201
    assert r.json() == {"evaluacion_id": 1, "estado": "en_evaluacion"}


def test_vacante_inexistente_404(client):
    assert postular(client, vacante_id="nada").status_code == 404


def test_no_pdf_415_por_content_type(client):
    assert postular(client, content_type="text/plain").status_code == 415


def test_no_pdf_415_por_magic_bytes(client):
    assert postular(client, pdf=b"MZ no soy pdf").status_code == 415


def test_pdf_mayor_5mb_413(client):
    assert postular(client, pdf=PDF + b"0" * MB5).status_code == 413


def test_content_length_enorme_413_antes_de_parsear(client, uploads):
    # Con content-type inválido, solo un corte previo al parseo devuelve 413 (no 415).
    r = postular(client, pdf=b"x" * (6 * 1024 * 1024), content_type="text/plain")
    assert r.status_code == 413
    assert list(uploads.iterdir()) == []


def test_pdf_exactamente_5mb_ok(client):
    assert postular(client, pdf=PDF + b"0" * (MB5 - len(PDF))).status_code == 201


def test_contacto_invalido_422(client):
    for kw in (dict(email="no-es-email"), dict(email="a@b"), dict(email="a b@c.co"),
               dict(email="a" * 250 + "@b.co"), dict(nombre=""), dict(nombre="n" * 201)):
        assert postular(client, **kw).status_code == 422, kw


def test_consentimiento_false_422(client):
    assert postular(client, consentimiento="false").status_code == 422


def test_consentimiento_ausente_422(client):
    r = client.post("/postulaciones", data={"vacante_id": "backend-jr", "nombre": "A", "email": "a@b.co"},
                    files={"pdf": ("hv.pdf", PDF, "application/pdf")})
    assert r.status_code == 422


def _rechazos():
    return [
        dict(consentimiento="false"),
        dict(content_type="text/plain"),
        dict(pdf=b"MZ no soy pdf"),
        dict(pdf=PDF + b"0" * MB5),
        dict(vacante_id="nada"),
    ]


def test_rechazo_no_persiste_nada(client, engine, uploads):
    for kw in _rechazos():
        assert postular(client, **kw).status_code >= 400
    with Session(engine) as s:
        assert s.exec(select(Candidato)).all() == []
        assert s.exec(select(Postulacion)).all() == []
        assert s.exec(select(Evaluacion)).all() == []
    assert list(uploads.iterdir()) == []


def test_rechazos_quedan_en_auditoria_sin_datos_personales(client, engine):
    for kw in _rechazos():
        postular(client, **kw)
    with Session(engine) as s:
        filas = s.exec(select(Auditoria)).all()
    assert len(filas) == len(_rechazos())
    assert {f.evento for f in filas} == {"postulacion_rechazada"}
    assert all(f.evaluacion_id is None for f in filas)
    assert not any("Ana" in f.detalle or "ana@example.com" in f.detalle for f in filas)
    assert {json.loads(f.detalle)["status"] for f in filas} == {422, 415, 413, 404}


def test_uploads_dir_se_lee_perezosamente_del_entorno(monkeypatch, tmp_path):
    from app.routes import UPLOADS_DIR

    monkeypatch.delenv("UPLOADS_DIR", raising=False)
    assert get_uploads_dir() == UPLOADS_DIR
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path))
    assert get_uploads_dir() == tmp_path


def test_fallo_de_bd_borra_pdf_y_hace_rollback(engine, uploads):
    class SesionRota(Session):
        def commit(self):
            raise RuntimeError("BD caída")

    def _session():
        with SesionRota(engine) as s:
            yield s

    app.dependency_overrides[get_session] = _session
    app.dependency_overrides[get_uploads_dir] = lambda: uploads
    try:
        r = postular(TestClient(app, raise_server_exceptions=False))
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 500
    assert list(uploads.iterdir()) == []
    with Session(engine) as s:
        assert s.exec(select(Candidato)).all() == []


def test_creada_incluye_consentimiento_at_en_auditoria(client, engine):
    postular(client)
    with Session(engine) as s:
        a = s.exec(select(Auditoria)).one()
        p = s.exec(select(Postulacion)).one()
    # SQLite devuelve la fecha sin zona; el detalle conserva la zona UTC.
    assert json.loads(a.detalle)["consentimiento_at"].startswith(p.consentimiento_at.isoformat())


def test_persiste_consentimiento_y_contacto_aparte(client, engine):
    postular(client)
    with Session(engine) as s:
        p = s.exec(select(Postulacion)).one()
        c = s.get(Candidato, p.candidato_id)
        assert p.consentimiento_at is not None
        assert (c.nombre, c.email) == ("Ana Pérez", "ana@example.com")
        ev = s.exec(select(Evaluacion)).one()
        assert "Ana" not in str(ev.perfil) and "ana@example.com" not in str(ev.perfil)


def test_auditoria_de_evaluacion(client, engine):
    postular(client)
    with Session(engine) as s:
        a = s.exec(select(Auditoria)).one()
        assert a.evento == "evaluacion_creada"
        assert a.timestamp is not None
        assert a.evaluacion_id == 1


def test_path_traversal_no_escapa_de_uploads(client, engine, uploads, tmp_path):
    r = postular(client, filename="../../evil.pdf")
    assert r.status_code == 201
    archivos = list(uploads.iterdir())
    assert len(archivos) == 1
    assert archivos[0].read_bytes() == PDF
    assert "evil" not in archivos[0].name
    assert not (tmp_path / "evil.pdf").exists()
    with Session(engine) as s:
        p = s.exec(select(Postulacion)).one()
        assert "evil" not in p.pdf_path and ".." not in p.pdf_path
