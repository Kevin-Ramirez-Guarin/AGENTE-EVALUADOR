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
        _vacante(nivel_educativo_min="doctor")
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


def test_idioma_es_modelo_con_campos_requeridos():
    from app.models import Idioma

    assert Idioma(idioma="inglés", nivel="B1").nivel == "B1"
    with pytest.raises(ValidationError):
        Idioma(idioma="inglés")
    assert isinstance(_perfil().idiomas[0], Idioma)
    with pytest.raises(ValidationError):
        _perfil(idiomas=[{"solo": "dict"}])


def test_pesos_negativos_que_suman_uno_fallan():
    with pytest.raises(ValidationError):
        _vacante(pesos={"tecnico": 1.5, "experiencia": -0.5, "blandas": 0, "educacion": 0, "idiomas": 0})


def test_puntajes_fuera_de_0_100_fallan():
    base = dict(
        puntajes_por_criterio={"tecnico": 90},
        veredicto_sugerido=Veredicto.ENTREVISTA,
        cumple_obligatorios=True,
        explicacion="ok",
    )
    for total in (-1, 100.1):
        with pytest.raises(ValidationError):
            ResultadoEvaluacion(puntaje_total=total, **base)
    with pytest.raises(ValidationError):
        ResultadoEvaluacion(**{**base, "puntajes_por_criterio": {"tecnico": 101}}, puntaje_total=50)
    assert ResultadoEvaluacion(puntaje_total=100, **base).puntaje_total == 100


def test_criterio_detalle_y_criterios_por_defecto_vacios():
    from app.models import CriterioDetalle

    base = dict(puntaje_total=50, puntajes_por_criterio={}, veredicto_sugerido=Veredicto.NO_CONTINUA,
                cumple_obligatorios=False, explicacion="ok")
    assert ResultadoEvaluacion(**base).criterios == []
    c = CriterioDetalle(criterio="tecnico", puntaje=70, peso=0.45, nota="ok")
    assert c.cumplidos == [] and c.faltantes == [] and c.evidencias == []
    for malo in ({"criterio": "otro"}, {"puntaje": 101}, {"peso": 1.1}):
        with pytest.raises(ValidationError):
            CriterioDetalle(**{"criterio": "tecnico", "puntaje": 1, "peso": 0.1, "nota": "x", **malo})
