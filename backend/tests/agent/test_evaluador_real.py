"""Costura evaluador.py <-> agente: selección por EVALUADOR y paso de todas las vacantes."""
import pytest

from app import evaluador
from app.main import _cargar_vacantes


def test_get_evaluador_es_el_real_por_defecto(monkeypatch):
    monkeypatch.delenv("EVALUADOR", raising=False)
    assert evaluador.get_evaluador() is evaluador.evaluador_real


@pytest.mark.parametrize("valor", ["falso", "FALSO", " falso "])
def test_get_evaluador_falso_si_la_variable_lo_pide(monkeypatch, valor):
    monkeypatch.setenv("EVALUADOR", valor)
    assert evaluador.get_evaluador() is evaluador.evaluador_falso


def test_get_evaluador_real_con_otro_valor(monkeypatch):
    monkeypatch.setenv("EVALUADOR", "real")
    assert evaluador.get_evaluador() is evaluador.evaluador_real


def test_evaluador_real_pasa_todas_las_vacantes_al_agente(monkeypatch):
    llamadas = []
    monkeypatch.setattr(evaluador, "evaluar_hv", lambda *a, **k: llamadas.append(a) or "salida")
    vacantes = _cargar_vacantes()
    assert evaluador.evaluador_real(b"pdf", vacantes[1]) == "salida"
    assert llamadas == [(b"pdf", vacantes[1], vacantes)]
