"""Orquestación del agente con un LLM falso que emite tool calls (sin gastar créditos)."""
import json
import logging
from pathlib import Path

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from app import agent, scoring
from app.agent import PdfInvalidoError, PdfSinTextoError, evaluar_hv
from app.models import Habilidad, PerfilCandidato, Vacante

RAIZ = Path(__file__).resolve().parents[3]
PDF = (RAIZ / "samples" / "hv_backend_fuerte_1.pdf").read_bytes()
PDF_ESCANEADO = (RAIZ / "samples" / "hv_escaneada.pdf").read_bytes()
VACANTES = [Vacante(**v) for v in json.loads((RAIZ / "backend" / "data" / "vacantes.json").read_text(encoding="utf-8"))]
BACKEND, FRONTEND = VACANTES[0], VACANTES[1]
HERRAMIENTAS = ["extraer_texto_pdf", "extraer_perfil", "evaluar_contra_vacante", "comparar_otras_vacantes"]


def _h(n):
    return Habilidad(nombre=n, nivel="avanzado", evidencia=f"experiencia con {n}")


PERFIL = PerfilCandidato(
    habilidades_tecnicas=[_h(n) for n in ("Python", "SQL", "Git", "Docker", "Django", "Testing")],
    habilidades_blandas=[_h("Trabajo en equipo"), _h("Aprendizaje")],
    anios_experiencia=3, nivel_educativo="tecnologo", idiomas=[{"idioma": "inglés", "nivel": "B1"}],
    fortalezas=[], debilidades=[], resumen="r",
)


def _llamadas(nombres):
    msgs = [AIMessage(content="", tool_calls=[{"name": n, "args": {}, "id": f"id{i}"}]) for i, n in enumerate(nombres)]
    return msgs + [AIMessage(content="Listo: el puntaje es 7 y no debe entrevistarse.")]


class LlmFalso(GenericFakeChatModel):
    """GenericFakeChatModel no implementa bind_tools; aquí lo ignoramos y devolvemos los mensajes guiados."""
    perfil: PerfilCandidato = PERFIL
    falla: bool = False
    perfil_falla: bool = False
    llamadas_perfil: list = []

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, *a, **kw):
        if self.falla:
            raise RuntimeError("Gemini no responde")
        return super()._generate(*a, **kw)

    def with_structured_output(self, schema, **kwargs):
        def extraer(_):
            self.llamadas_perfil.append(1)
            if self.perfil_falla:
                raise RuntimeError("falló la extracción")
            return self.perfil

        return RunnableLambda(extraer)


def _llm(nombres, **kw):
    return LlmFalso(messages=iter(_llamadas(nombres)), **kw)


def test_agente_completo_devuelve_lo_calculado_por_python_no_lo_dicho_por_el_llm():
    perfil, res = evaluar_hv(PDF, BACKEND, VACANTES, llm=_llm(HERRAMIENTAS))
    esperado = scoring.evaluar(PERFIL, BACKEND)
    assert perfil == PERFIL
    assert res.puntaje_total == esperado.puntaje_total != 7  # el LLM dijo 7; se ignora
    assert res.criterios == esperado.criterios


def test_sin_llamar_herramientas_activa_el_respaldo_y_lo_registra(caplog):
    with caplog.at_level(logging.WARNING, logger="app.agent"):
        perfil, res = evaluar_hv(PDF, BACKEND, VACANTES, llm=_llm([]))
    assert res == scoring.evaluar(PERFIL, BACKEND)
    assert any("respaldo" in r.message.lower() for r in caplog.records)


def test_contexto_incompleto_activa_el_respaldo(caplog):
    with caplog.at_level(logging.WARNING, logger="app.agent"):
        _, res = evaluar_hv(PDF, BACKEND, VACANTES, llm=_llm(HERRAMIENTAS[:2]))
    assert res == scoring.evaluar(PERFIL, BACKEND)
    assert any("respaldo" in r.message.lower() for r in caplog.records)


def test_si_el_agente_falla_usa_el_respaldo(caplog):
    with caplog.at_level(logging.WARNING, logger="app.agent"):
        _, res = evaluar_hv(PDF, BACKEND, VACANTES, llm=_llm([], falla=True))
    assert res == scoring.evaluar(PERFIL, BACKEND)
    assert any("respaldo" in r.message.lower() for r in caplog.records)


def test_modo_pipeline_no_usa_el_agente(monkeypatch):
    monkeypatch.setenv("MODO_EVALUACION", "pipeline")
    monkeypatch.setattr(agent, "create_agent", lambda *a, **k: pytest.fail("no debe crear el agente"))
    perfil, res = evaluar_hv(PDF, BACKEND, VACANTES, llm=_llm([]))
    assert res == scoring.evaluar(PERFIL, BACKEND)


def test_modo_por_defecto_es_agente(monkeypatch):
    monkeypatch.delenv("MODO_EVALUACION", raising=False)
    llamado = []
    real = agent.create_agent
    monkeypatch.setattr(agent, "create_agent", lambda *a, **k: llamado.append(1) or real(*a, **k))
    evaluar_hv(PDF, BACKEND, VACANTES, llm=_llm(HERRAMIENTAS))
    assert llamado


def test_respaldo_reutiliza_el_perfil_ya_extraido():
    llm = _llm(HERRAMIENTAS[:2])
    _, res = evaluar_hv(PDF, BACKEND, VACANTES, llm=llm)
    assert res == scoring.evaluar(PERFIL, BACKEND)
    assert len(llm.llamadas_perfil) == 1  # el respaldo no vuelve a llamar a Gemini


@pytest.mark.parametrize("nombres", [HERRAMIENTAS, []])
def test_fallo_de_extraer_perfil_se_propaga_sin_repetir_la_llamada(nombres):
    llm = _llm(nombres, perfil_falla=True)
    with pytest.raises(RuntimeError, match="extracción"):
        evaluar_hv(PDF, BACKEND, VACANTES, llm=llm)
    assert len(llm.llamadas_perfil) == 1


def test_prompt_del_orquestador_es_corto():
    assert len(agent.PROMPT_AGENTE) < 600


def test_mejor_vacante_alternativa_sale_de_la_herramienta():
    _, res = evaluar_hv(PDF, FRONTEND, VACANTES, llm=_llm(HERRAMIENTAS))
    assert res.mejor_vacante_alternativa == "backend-jr"


def test_respaldo_tambien_calcula_la_alternativa():
    _, res = evaluar_hv(PDF, FRONTEND, VACANTES, llm=_llm([]))
    assert res.mejor_vacante_alternativa == "backend-jr"


@pytest.mark.parametrize("nombres", [HERRAMIENTAS, []])
def test_pdf_invalido_se_propaga_con_o_sin_agente(nombres):
    with pytest.raises(PdfInvalidoError):
        evaluar_hv(b"esto no es un pdf", BACKEND, VACANTES, llm=_llm(nombres))


@pytest.mark.parametrize("nombres", [HERRAMIENTAS, []])
def test_pdf_sin_texto_se_propaga_con_o_sin_agente(nombres):
    with pytest.raises(PdfSinTextoError):
        evaluar_hv(PDF_ESCANEADO, BACKEND, VACANTES, llm=_llm(nombres))
