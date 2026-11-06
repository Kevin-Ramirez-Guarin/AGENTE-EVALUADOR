import pytest
from pydantic import ValidationError

from app.models import (
    Habilidad,
    PerfilCandidato,
    ResultadoEvaluacion,
    Vacante,
    Veredicto,
)

PESOS_OK = {"tecnico": 0.45, "experiencia": 0.25, "blandas": 0.15, "educacion": 0.10, "idiomas": 0.05}


def _vacante(**cambios):
    base = dict(
        id="x",
        titulo="Dev",
        requisitos_obligatorios=["Python"],
        deseables=[],
        blandas=[],
        experiencia_min_anios=0,
        nivel_educativo_min="tecnico",
        idiomas=[],
        pesos=PESOS_OK,
    )
    return Vacante(**{**base, **cambios})


def _perfil(**cambios):
    base = dict(
        habilidades_tecnicas=[Habilidad(nombre="Python", nivel="avanzado", evidencia="5 años con Python")],
        habilidades_blandas=[],
        anios_experiencia=2,
        nivel_educativo="profesional",
        idiomas=[{"idioma": "inglés", "nivel": "B2"}],
        fortalezas=["a"],
        debilidades=[],
        resumen="ok",
    )
    return PerfilCandidato(**{**base, **cambios})


def test_vacante_valida():
    assert _vacante().id == "x"


def test_pesos_que_no_suman_uno_fallan():
    with pytest.raises(ValidationError):
        _vacante(pesos={**PESOS_OK, "tecnico": 0.50})


def test_pesos_con_error_de_flotante_se_aceptan():
    assert _vacante(pesos={"tecnico": 0.1, "experiencia": 0.2, "blandas": 0.3, "educacion": 0.2, "idiomas": 0.2})


def test_nivel_educativo_invalido_falla():
    with pytest.raises(ValidationError):
        _vacante(nivel_educativo="doctor")
    with pytest.raises(ValidationError):
        _perfil(nivel_educativo="doctor")


def test_nivel_de_habilidad_invalido_falla():
    with pytest.raises(ValidationError):
        Habilidad(nombre="x", nivel="experto", evidencia="y")


def test_perfil_valido_y_limite_de_fortalezas():
    assert _perfil().anios_experiencia == 2
    with pytest.raises(ValidationError):
        _perfil(fortalezas=["a", "b", "c", "d"])
    with pytest.raises(ValidationError):
        _perfil(debilidades=["a", "b", "c", "d"])


def test_veredicto_valores():
    assert {v.value for v in Veredicto} == {"ENTREVISTA", "REVISION_HUMANA", "NO_CONTINUA"}


def test_resultado_evaluacion_alternativa_es_opcional():
    r = ResultadoEvaluacion(
        puntaje_total=80,
        puntajes_por_criterio={"tecnico": 90},
        veredicto_sugerido=Veredicto.ENTREVISTA,
        cumple_obligatorios=True,
        explicacion="ok",
    )
    assert r.mejor_vacante_alternativa is None
