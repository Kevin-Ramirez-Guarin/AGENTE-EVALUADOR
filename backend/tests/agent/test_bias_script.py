"""scripts/bias_test.py: lógica pura y orquestación con un evaluador falso (sin Gemini, sin .env)."""
import os

import pytest

from app import agent
from app.models import PerfilCandidato, ResultadoEvaluacion
from scripts import bias_test
from scripts.variantes_hv import VARIANTES_BIAS as VARIANTES


def _fila(nombre, puntajes, veredictos=None):
    return {"variante": nombre, "puntajes": puntajes, "media": sum(puntajes) / len(puntajes),
            "veredictos": veredictos or ["ENTREVISTA"] * len(puntajes)}


def test_diferencia_maxima_entre_medias():
    assert bias_test.diferencia_maxima([_fila("a", [80, 82]), _fila("b", [70, 74]), _fila("c", [79])]) == pytest.approx(9.0)
    assert bias_test.diferencia_maxima([_fila("a", [80])]) == 0


def test_evaluar_variantes_corre_n_veces_por_variante_con_su_identidad():
    vistos = []

    def falso(pdf, identidad):
        vistos.append(identidad["nombre"])
        return 80.0 + len(vistos) % 2, "ENTREVISTA"

    filas = bias_test.evaluar_variantes(falso, VARIANTES, corridas=2)
    assert len(filas) == len(VARIANTES) and len(vistos) == 2 * len(VARIANTES)
    assert all(len(f["puntajes"]) == 2 and f["veredictos"] == ["ENTREVISTA"] * 2 for f in filas)
    assert filas[0]["variante"].startswith("base")


def test_el_reporte_tiene_tabla_diferencia_y_veredicto_del_criterio():
    filas = [_fila("María", [80, 82]), _fila("Juan", [78, 80], ["ENTREVISTA", "REVISION_HUMANA"])]
    md = bias_test.generar_reporte(filas, anonimizado=True, corridas=2)
    assert "| Variante | Puntaje medio | Desv. entre corridas | Veredicto |" in md
    assert "| María | 81.0 | 1.0 | ENTREVISTA |" in md and "| Juan | 79.0 | 1.0 | ENTREVISTA / REVISION_HUMANA |" in md
    assert "Diferencia máxima entre variantes: 2.0" in md and "< 5" in md and "CUMPLE" in md and "NO CUMPLE" not in md
    assert "con anonimizador" in md.lower()
    assert "Ruido del LLM" in md and "1.0" in md.split("Ruido del LLM")[1].splitlines()[0]
    assert "idéntico" in md and "--sin-anonimizar" in md  # con anonimizador la diferencia mide el ruido


def test_el_reporte_sin_anonimizador_no_dice_que_el_texto_es_identico():
    md = bias_test.generar_reporte([_fila("a", [90]), _fila("b", [70])], anonimizado=False, corridas=1)
    assert "idéntico" not in md and "Ruido del LLM" in md


def test_por_defecto_son_3_corridas():
    assert bias_test.CORRIDAS_POR_DEFECTO == 3


def test_las_variantes_cambian_un_factor_a_la_vez_mas_una_combinada():
    factores = ("nombre", "genero", "origen", "edad")
    base, *resto = VARIANTES
    assert base["factor"] == "base"
    for v in resto[:-1]:
        cambiados = {k for k in factores if v[k] != base[k]}
        assert cambiados == {v["factor"]}, v["factor"]
    assert {v["factor"] for v in resto[:-1]} == set(factores)
    combinada = resto[-1]
    assert combinada["factor"] == "combinada" and all(combinada[k] != base[k] for k in factores)
    assert len(VARIANTES) >= 6


def test_el_reporte_marca_incumplimiento_y_modo_sin_anonimizador():
    md = bias_test.generar_reporte([_fila("a", [90]), _fila("b", [70])], anonimizado=False, corridas=1)
    assert "NO CUMPLE" in md and "SIN anonimizador" in md


def test_help_funciona_sin_env(capsys):
    with pytest.raises(SystemExit) as e:
        bias_test.main(["--help"])
    assert e.value.code == 0 and "--sin-anonimizar" in capsys.readouterr().out


def _falso(llamadas):
    def evaluar_hv(pdf, vacante, vacantes, llm=None, identidad=None):
        llamadas.append((identidad, os.environ.get("MODO_EVALUACION"), agent.anonimizar))
        perfil = PerfilCandidato(habilidades_tecnicas=[], habilidades_blandas=[], anios_experiencia=0, nivel_educativo="bachiller",
                                 idiomas=[], fortalezas=[], debilidades=[], resumen="r")
        res = ResultadoEvaluacion(puntaje_total=70, puntajes_por_criterio={}, veredicto_sugerido="REVISION_HUMANA",
                                  cumple_obligatorios=True, explicacion="e")
        return perfil, res
    return evaluar_hv


@pytest.mark.parametrize("sin_anonimizar", [False, True])
def test_main_escribe_el_reporte_en_modo_pipeline_y_restaura_el_entorno(monkeypatch, tmp_path, sin_anonimizar):
    llamadas, salida = [], tmp_path / "docs" / "sesgo" / "r.md"
    monkeypatch.setattr(agent, "evaluar_hv", _falso(llamadas))
    monkeypatch.setenv("MODO_EVALUACION", "agente")
    real = agent.anonimizar
    bias_test.main(["--corridas", "2", "--salida", str(salida)] + (["--sin-anonimizar"] if sin_anonimizar else []))
    assert len(llamadas) == 2 * len(VARIANTES)
    assert {m for _, m, _ in llamadas} == {"pipeline"}
    assert all((a is real) != sin_anonimizar for _, _, a in llamadas)  # con la bandera, anonimizar es un paso nulo
    assert all(i["nombre"] for i, _, _ in llamadas)
    assert agent.anonimizar is real and os.environ["MODO_EVALUACION"] == "agente"
    texto = salida.read_text(encoding="utf-8")
    assert "Diferencia máxima" in texto and ("SIN anonimizador" in texto) == sin_anonimizar


def test_salida_por_defecto_depende_del_modo():
    assert bias_test.salida_por_defecto(True).name == "resultados.md"
    assert bias_test.salida_por_defecto(False).name == "resultados_sin_anonimizar.md"
    assert bias_test.salida_por_defecto(True).parent.name == "sesgo"
