import json
from datetime import datetime, timedelta, timezone

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.db import Auditoria, Candidato, Evaluacion, Postulacion
from scripts.purgar_datos import ELIMINADO, main, purgar

AHORA = datetime(2026, 11, 1, tzinfo=timezone.utc)


SECRETO = "Trabajó en Acme Bogotá con Laura Restrepo"
PERFIL = {"resumen": SECRETO, "fortalezas": [SECRETO], "debilidades": [SECRETO],
          "habilidades_tecnicas": [{"nombre": "Python", "evidencia": SECRETO}]}
RESULTADO = {"puntaje_total": 80, "puntajes_por_criterio": {"tecnico": 80.0},
             "veredicto_sugerido": "ENTREVISTA", "cumple_obligatorios": True,
             "explicacion": SECRETO, "mejor_vacante_alternativa": SECRETO,
             "criterios": [{"criterio": "tecnico", "puntaje": 80.0, "peso": 0.5,
                            "cumplidos": ["Python"], "faltantes": ["Docker"],
                            "evidencias": [SECRETO], "nota": SECRETO}]}


@pytest.fixture
def entorno(tmp_path):
    eng = create_engine(f"sqlite:///{tmp_path / 'p.db'}")
    SQLModel.metadata.create_all(eng)
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    with Session(eng) as s:
        for i, dias in enumerate((200, 10, 200, 200), start=1):
            (uploads / f"{i}.pdf").write_bytes(b"%PDF-1.4")
            c = Candidato(nombre=f"Persona {i}", email=f"p{i}@example.com")
            s.add(c)
            s.flush()
            p = Postulacion(candidato_id=c.id, vacante_id="backend-jr", pdf_path=f"{i}.pdf",
                            consentimiento_at=AHORA, creada_at=AHORA - timedelta(days=dias))
            s.add(p)
            s.flush()
            estado = {3: "en_evaluacion", 4: "error_evaluacion"}.get(i, "decidida")
            s.add(Evaluacion(postulacion_id=p.id, puntaje_total=80, perfil=dict(PERFIL),
                             resultado=dict(RESULTADO), veredicto_ia="ENTREVISTA",
                             veredicto_final="ENTREVISTA", estado=estado,
                             decidido_por="rec"))
        s.commit()
    return eng, uploads


def test_purga_solo_las_viejas_y_conserva_evaluaciones(entorno):
    eng, uploads = entorno
    with Session(eng) as s:
        assert purgar(s, uploads, 180, ahora=AHORA) == 1
    assert not (uploads / "1.pdf").exists() and (uploads / "2.pdf").exists()
    with Session(eng) as s:
        c1, c2 = s.get(Candidato, 1), s.get(Candidato, 2)
        assert (c1.nombre, c1.email) == (ELIMINADO, ELIMINADO)
        assert c2.nombre == "Persona 2"
        assert s.get(Postulacion, 1).pdf_path == ELIMINADO
        evs = s.exec(select(Evaluacion)).all()
        assert len(evs) == 4 and evs[0].decidido_por == "rec"
        assert evs[0].puntaje_total == 80 and evs[0].veredicto_final == "ENTREVISTA"
        assert evs[0].resultado["veredicto_sugerido"] == "ENTREVISTA"
        assert evs[0].resultado["puntajes_por_criterio"] == {"tecnico": 80.0}
        assert evs[0].resultado["criterios"] == [{"criterio": "tecnico", "puntaje": 80.0, "peso": 0.5}]
        a = s.exec(select(Auditoria)).one()
        assert a.evento == "datos_purgados" and a.evaluacion_id == 1
        assert "Persona" not in a.detalle and json.loads(a.detalle)["dias"] == 180


def test_dry_run_no_cambia_nada(entorno):
    eng, uploads = entorno
    with Session(eng) as s:
        assert purgar(s, uploads, 180, dry_run=True, ahora=AHORA) == 1
    assert (uploads / "1.pdf").exists()
    with Session(eng) as s:
        assert s.get(Candidato, 1).nombre == "Persona 1"
        assert s.exec(select(Auditoria)).all() == []


def test_es_idempotente_y_tolera_pdf_ya_borrado(entorno):
    eng, uploads = entorno
    (uploads / "1.pdf").unlink()
    with Session(eng) as s:
        assert purgar(s, uploads, 180, ahora=AHORA) == 1
        assert purgar(s, uploads, 180, ahora=AHORA) == 0


def test_main_cli(entorno, monkeypatch, capsys):
    eng, uploads = entorno
    monkeypatch.setattr("scripts.purgar_datos.get_engine", lambda: eng)
    monkeypatch.setattr("scripts.purgar_datos.get_uploads_dir", lambda: uploads)
    assert main(["--dias", "1", "--dry-run"]) == 0
    assert "2" in capsys.readouterr().out
    assert (uploads / "2.pdf").exists()
    assert main([]) == 0


def test_purga_redacta_perfil_y_resultado_sin_texto_de_la_hv(entorno):
    eng, uploads = entorno
    with Session(eng) as s:
        purgar(s, uploads, 180, ahora=AHORA)
    with Session(eng) as s:
        ev = s.exec(select(Evaluacion).where(Evaluacion.postulacion_id == 1)).one()
        volcado = json.dumps([ev.perfil, ev.resultado], ensure_ascii=False)
        for texto in ("Acme", "Laura", "Bogotá", "Python", "Docker"):
            assert texto not in volcado
        assert ev.perfil is None
        sin_purgar = s.get(Evaluacion, 2)  # la de 10 días conserva todo
        assert SECRETO in json.dumps(sin_purgar.perfil, ensure_ascii=False)


def test_no_purga_evaluaciones_en_curso_ni_con_error(entorno):
    eng, uploads = entorno
    with Session(eng) as s:
        assert purgar(s, uploads, 1, ahora=AHORA) == 2  # solo 1 y 2 (decididas)
    assert (uploads / "3.pdf").exists() and (uploads / "4.pdf").exists()
    with Session(eng) as s:
        assert s.get(Candidato, 3).nombre == "Persona 3"
        assert s.get(Candidato, 4).email == "p4@example.com"
        assert s.get(Evaluacion, 3).perfil == PERFIL
