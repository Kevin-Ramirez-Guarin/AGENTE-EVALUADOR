"""Caja blanca de scoring.py (PLAN.md §5). Sin LLM: perfiles armados a mano."""
import json
from pathlib import Path

import pytest

from app.models import Habilidad, PerfilCandidato, Vacante, Veredicto
from app.scoring import _veredicto, evaluar, mejor_vacante

DATOS = Path(__file__).resolve().parents[2] / "data" / "vacantes.json"
VACANTES = [Vacante(**v) for v in json.loads(DATOS.read_text(encoding="utf-8"))]
PESOS = {"tecnico": 0.45, "experiencia": 0.25, "blandas": 0.15, "educacion": 0.10, "idiomas": 0.05}


def hab(nombre, evidencia=""):
    return Habilidad(nombre=nombre, nivel="intermedio", evidencia=evidencia or f"uso {nombre}")


def perfil(tec=(), blandas=(), anios=0, edu="bachiller", idiomas=()):
    return PerfilCandidato(
        habilidades_tecnicas=[h if isinstance(h, Habilidad) else hab(h) for h in tec],
        habilidades_blandas=[hab(b) for b in blandas],
        anios_experiencia=anios,
        nivel_educativo=edu,
        idiomas=[{"idioma": i, "nivel": n} for i, n in idiomas],
        fortalezas=[], debilidades=[], resumen="r",
    )


def vacante(**kw):
    base = dict(id="v", titulo="V", requisitos_obligatorios=["Python"], deseables=[], blandas=[],
                experiencia_min_anios=1, nivel_educativo_min="bachiller", idiomas=[], pesos=PESOS)
    return Vacante(**{**base, **kw})


def crit(res, nombre):
    return next(c for c in res.criterios if c.criterio == nombre)


# --- técnico ---------------------------------------------------------------
def test_tecnico_pesa_70_obligatorios_y_30_deseables():
    v = vacante(requisitos_obligatorios=["Python"], deseables=["Docker"])
    assert evaluar(perfil(["Python"]), v).puntajes_por_criterio["tecnico"] == 70
    assert evaluar(perfil(["Python", "Docker"]), v).puntajes_por_criterio["tecnico"] == 100
    assert evaluar(perfil(["Docker"]), v).puntajes_por_criterio["tecnico"] == 30


def test_tecnico_parcial_de_obligatorios():
    v = vacante(requisitos_obligatorios=["Python", "SQL", "Git"], deseables=["Docker"])
    res = evaluar(perfil(["Python", "SQL", "Docker"]), v)
    assert res.puntajes_por_criterio["tecnico"] == pytest.approx(76.7, abs=0.05)
    c = crit(res, "tecnico")
    assert c.faltantes == ["Git"]
    assert set(c.cumplidos) == {"Python", "SQL", "Docker"}


def test_sin_deseables_cuenta_como_cumplido_el_30():
    assert evaluar(perfil(["Python"]), vacante()).puntajes_por_criterio["tecnico"] == 100


def test_alternativas_con_barra():
    v = vacante(requisitos_obligatorios=["FastAPI/Django"])
    assert evaluar(perfil(["Django"]), v).cumple_obligatorios
    assert evaluar(perfil(["fastapi"]), v).cumple_obligatorios
    assert not evaluar(perfil(["Flask"]), v).cumple_obligatorios


def test_sinonimos():
    v = vacante(requisitos_obligatorios=["SQL"])
    assert evaluar(perfil(["PostgreSQL"]), v).cumple_obligatorios


def test_coincide_por_evidencia_aunque_el_nombre_no():
    v = vacante(requisitos_obligatorios=["Git"])
    assert evaluar(perfil([hab("Control de versiones", "Uso Git y GitHub a diario")]), v).cumple_obligatorios


def test_ignora_tildes_y_mayusculas():
    v = vacante(requisitos_obligatorios=["Estadística básica"])
    assert evaluar(perfil(["ESTADISTICA BASICA"]), v).cumple_obligatorios


def test_no_coincide_por_subcadena():
    v = vacante(requisitos_obligatorios=["Git"])
    assert not evaluar(perfil(["Marketing digital"]), v).cumple_obligatorios


def test_blandas_se_calculan_como_el_tecnico():
    v = vacante(blandas=["Trabajo en equipo", "Aprendizaje"])
    res = evaluar(perfil(["Python"], blandas=["Trabajo en equipo"]), v)
    assert res.puntajes_por_criterio["blandas"] == 50
    assert crit(res, "blandas").faltantes == ["Aprendizaje"]
    assert evaluar(perfil(["Python"]), vacante()).puntajes_por_criterio["blandas"] == 100  # sin blandas pedidas


# --- experiencia y educación -----------------------------------------------
@pytest.mark.parametrize("anios,minimo,esperado", [(0.5, 1, 50), (3, 1, 100), (0, 0, 100), (2, 0, 100), (0, 2, 0)])
def test_experiencia(anios, minimo, esperado):
    res = evaluar(perfil(["Python"], anios=anios), vacante(experiencia_min_anios=minimo))
    assert res.puntajes_por_criterio["experiencia"] == esperado


@pytest.mark.parametrize("cand,minimo,esperado", [
    ("bachiller", "profesional", 25), ("tecnico", "profesional", 50), ("tecnologo", "profesional", 75),
    ("profesional", "profesional", 100), ("posgrado", "profesional", 100), ("posgrado", "bachiller", 100),
])
def test_educacion_sigue_el_orden(cand, minimo, esperado):
    res = evaluar(perfil(["Python"], edu=cand), vacante(nivel_educativo_min=minimo))
    assert res.puntajes_por_criterio["educacion"] == esperado


# --- idiomas ---------------------------------------------------------------
@pytest.mark.parametrize("idiomas,pedido,esperado", [
    ([("inglés", "B1")], "B1", 100), ([("Ingles", "C2")], "B1", 100), ([("inglés", "B2")], "A2", 100),
    ([("inglés", "A1")], "B1", pytest.approx(33.3, abs=0.05)),
    ([("francés", "C1")], "B1", 0), ([], "B1", 0), ([("inglés", "básico")], "B1", 0),
    ([("inglés", "nativo")], "C2", 100),
])
def test_idiomas(idiomas, pedido, esperado):
    req = [{"idioma": "inglés", "nivel": pedido}]
    res = evaluar(perfil(["Python"], idiomas=idiomas), vacante(idiomas=req))
    assert res.puntajes_por_criterio["idiomas"] == esperado


def test_idiomas_sin_requisito_vale_100():
    assert evaluar(perfil(["Python"]), vacante()).puntajes_por_criterio["idiomas"] == 100


# --- total, knock-out y veredicto -----------------------------------------
def test_perfil_perfecto_100_entrevista():
    p = perfil(["Python"], anios=5, edu="posgrado")
    res = evaluar(p, vacante())
    assert res.puntaje_total == 100
    assert res.veredicto_sugerido == Veredicto.ENTREVISTA
    assert res.cumple_obligatorios


def test_total_pondera_con_pesos_y_redondea_a_un_decimal():
    # tecnico 100, experiencia 50, blandas 100, educacion 25, idiomas 100
    v = vacante(experiencia_min_anios=2, nivel_educativo_min="profesional")
    res = evaluar(perfil(["Python"], anios=1), v)
    assert res.puntaje_total == 80.0  # 45 + 12.5 + 15 + 2.5 + 5
    # redondeo a 1 decimal: experiencia 1/3 -> 100 - 0.25 * 66.667 = 83.333
    assert evaluar(perfil(["Python"], anios=1), vacante(experiencia_min_anios=3)).puntaje_total == 83.3


def test_knockout_topa_en_40():
    v = vacante(requisitos_obligatorios=["Python", "SQL"])
    res = evaluar(perfil(["Python"], anios=5, edu="posgrado"), v)
    assert res.puntaje_total == 40
    assert not res.cumple_obligatorios
    assert res.veredicto_sugerido == Veredicto.NO_CONTINUA


def test_knockout_no_sube_puntajes_bajos():
    res = evaluar(perfil(), vacante(blandas=["Empatía"], nivel_educativo_min="profesional"))
    assert res.puntaje_total < 40 and not res.cumple_obligatorios


@pytest.mark.parametrize("total,esperado", [
    (0, Veredicto.NO_CONTINUA), (54.9, Veredicto.NO_CONTINUA), (55, Veredicto.REVISION_HUMANA),
    (74.9, Veredicto.REVISION_HUMANA), (75, Veredicto.ENTREVISTA), (100, Veredicto.ENTREVISTA),
])
def test_bordes_del_veredicto(total, esperado):
    assert _veredicto(total) == esperado


# --- criterios y explicación ----------------------------------------------
def test_criterios_completos_ordenados_con_pesos_y_notas():
    res = evaluar(perfil([hab("Python", "5 años con Python")], anios=2, edu="tecnologo"), vacante())
    assert [c.criterio for c in res.criterios] == ["tecnico", "experiencia", "blandas", "educacion", "idiomas"]
    assert [c.peso for c in res.criterios] == list(PESOS.values())
    assert all(c.nota.strip() for c in res.criterios)
    assert all(c.puntaje == res.puntajes_por_criterio[c.criterio] for c in res.criterios)
    assert crit(res, "tecnico").evidencias == ["5 años con Python"]


def test_nota_faltante_es_respetuosa_y_menciona_lo_que_falta():
    nota = crit(evaluar(perfil(), vacante()), "tecnico").nota
    assert "Python" in nota


def test_explicacion_son_2_o_3_frases():
    for p in (perfil(["Python"], anios=3), perfil()):
        frases = [f for f in evaluar(p, vacante()).explicacion.split(". ") if f.strip()]
        assert 2 <= len(frases) <= 3


# --- mejor vacante ---------------------------------------------------------
V_OTRA = vacante(id="otra", requisitos_obligatorios=["Java"], deseables=["Rust"])  # 89.5 para un perfil con Java


def test_mejor_vacante_devuelve_otra_con_75_o_mas_y_mayor():
    p = perfil(["Java"], anios=3, edu="profesional")
    assert mejor_vacante(p, [vacante(requisitos_obligatorios=["Rust"]), V_OTRA], "v") == "otra"


def test_mejor_vacante_none_si_la_actual_es_la_mejor():
    p = perfil(["Python"], anios=3, edu="profesional")
    assert mejor_vacante(p, [vacante(), V_OTRA], "v") is None


def test_mejor_vacante_none_si_ninguna_llega_a_75():
    assert mejor_vacante(perfil(), [vacante(), V_OTRA], "v") is None


def test_mejor_vacante_con_actual_desconocida_y_elige_la_mas_alta():
    p = perfil(["Java", "Python"], anios=3, edu="profesional")
    mejor = vacante(id="mejor", requisitos_obligatorios=["Java"], deseables=["Python"])
    assert mejor_vacante(p, [V_OTRA, mejor], "no-existe") == "mejor"


def test_vacantes_reales_backend_fuerte():
    p = perfil(["Python", "SQL", "Git", "Docker", "Django", "pytest testing"], blandas=["Trabajo en equipo"],
               anios=3, edu="tecnologo", idiomas=[("inglés", "B1")])
    res = evaluar(p, VACANTES[0])
    assert res.veredicto_sugerido == Veredicto.ENTREVISTA
