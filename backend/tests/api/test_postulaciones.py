from sqlmodel import Session, select

from app.db import Auditoria, Candidato, Evaluacion, Postulacion
from tests.api.conftest import PDF, postular

MB5 = 5 * 1024 * 1024


def test_crear_postulacion_201(client):
    r = postular(client)
    assert r.status_code == 201
    assert r.json() == {"evaluacion_id": 1, "estado": "pendiente_revision"}


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


def test_consentimiento_false_422(client):
    assert postular(client, consentimiento="false").status_code == 422


def test_consentimiento_ausente_422(client):
    r = client.post("/postulaciones", data={"vacante_id": "backend-jr", "nombre": "A", "email": "a@b.co"},
                    files={"pdf": ("hv.pdf", PDF, "application/pdf")})
    assert r.status_code == 422


def test_rechazo_no_persiste_nada(client, engine, uploads):
    postular(client, consentimiento="false")
    postular(client, content_type="text/plain")
    with Session(engine) as s:
        assert s.exec(select(Candidato)).all() == []
    assert list(uploads.iterdir()) == []


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
