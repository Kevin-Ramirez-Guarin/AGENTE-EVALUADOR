"""El LLM solo ve texto anonimizado, en el agente y en el pipeline; contrato `identidad` del evaluador."""
import pytest

from app import agent, evaluador, scoring
from app.agent import evaluar_hv
from app.evaluador import evaluador_falso
from scripts.variantes_hv import VARIANTES, identidad_de, pdf_de
from tests.agent.test_agente_orquestacion import BACKEND, HERRAMIENTAS, PERFIL, VACANTES, LlmFalso, _llamadas

V = VARIANTES[0]
PDF = pdf_de(V)
IDENTIDAD = identidad_de(V)


class LlmEspia(LlmFalso):
    """Guarda el texto exacto que recibiría Gemini en la extracción del perfil."""
    recibidos: list = []

    def with_structured_output(self, schema, **kwargs):
        extraer = super().with_structured_output(schema, **kwargs)

        def espiar(mensajes):
            self.recibidos.append(mensajes[-1].content)  # el HumanMessage con la HV
            return extraer.invoke(mensajes)

        from langchain_core.runnables import RunnableLambda
        return RunnableLambda(espiar)


def _llm(nombres):
    return LlmEspia(messages=iter(_llamadas(nombres)), recibidos=[], llamadas_perfil=[])


def _sin_datos_de_identidad(texto):
    for dato in (V["nombre"], "María", "Gómez", V["email"], V["tel"], "maria.gomez", "Desarrolladora", "Ingeniera", "Edad"):
        assert dato.lower() not in texto.lower()


@pytest.mark.parametrize("modo", ["pipeline", "agente"])
def test_el_llm_no_recibe_nombre_correo_ni_telefono(monkeypatch, modo):
    monkeypatch.setenv("MODO_EVALUACION", modo)
    llm = _llm(HERRAMIENTAS if modo == "agente" else [])
    evaluar_hv(PDF, BACKEND, VACANTES, llm=llm, identidad=IDENTIDAD)
    assert len(llm.recibidos) == 1
    _sin_datos_de_identidad(llm.recibidos[0])
    assert "[PERSONA]" in llm.recibidos[0] and "Python" in llm.recibidos[0]


def test_el_respaldo_del_agente_tambien_anonimiza(monkeypatch):
    monkeypatch.setenv("MODO_EVALUACION", "agente")
    llm = _llm(HERRAMIENTAS[:1])  # solo extrae el texto; el respaldo extrae el perfil
    evaluar_hv(PDF, BACKEND, VACANTES, llm=llm, identidad=IDENTIDAD)
    _sin_datos_de_identidad(llm.recibidos[0])


def test_scoring_recibe_el_texto_anonimizado(monkeypatch):
    vistos = []
    real = scoring.evaluar
    monkeypatch.setenv("MODO_EVALUACION", "pipeline")
    monkeypatch.setattr(scoring, "evaluar", lambda p, v, texto=None: vistos.append(texto) or real(p, v, texto))
    evaluar_hv(PDF, BACKEND, VACANTES, llm=_llm([]), identidad=IDENTIDAD)
    assert vistos and all(t and "[PERSONA]" in t and "María" not in t for t in vistos)


def test_variantes_distintas_dan_el_mismo_resultado_con_un_llm_determinista(monkeypatch):
    monkeypatch.setenv("MODO_EVALUACION", "pipeline")
    salidas = {evaluar_hv(pdf_de(v), BACKEND, VACANTES, llm=_llm([]), identidad=identidad_de(v))[1].model_dump_json()
              for v in VARIANTES}
    assert len(salidas) == 1


def test_sin_anonimizar_si_se_filtra_la_identidad(monkeypatch):
    """Contraste: sin el anonimizador el LLM ve el nombre (así funciona `--sin-anonimizar`)."""
    monkeypatch.setenv("MODO_EVALUACION", "pipeline")
    monkeypatch.setattr(agent, "anonimizar", lambda texto, identidad=None: texto)
    llm = _llm([])
    evaluar_hv(PDF, BACKEND, VACANTES, llm=llm, identidad=IDENTIDAD)
    assert V["nombre"] in llm.recibidos[0]


def test_identidad_es_opcional():
    perfil, res = evaluar_hv(PDF, BACKEND, VACANTES, llm=_llm([]))
    assert perfil == PERFIL and 0 <= res.puntaje_total <= 100


# ── contrato con el track Plataforma ────────────────────────────────────────────
def test_evaluador_falso_acepta_identidad_como_keyword_opcional():
    base = evaluador_falso(PDF, BACKEND)
    assert evaluador_falso(PDF, BACKEND, identidad=IDENTIDAD) == base


def test_evaluador_real_pasa_la_identidad_al_agente(monkeypatch):
    llamadas = []
    monkeypatch.setattr(evaluador, "evaluar_hv", lambda *a, **k: llamadas.append((a, k)) or "salida")
    assert evaluador.evaluador_real(b"pdf", BACKEND, identidad=IDENTIDAD) == "salida"
    assert llamadas[0][1] == {"identidad": IDENTIDAD}
    evaluador.evaluador_real(b"pdf", BACKEND)
    assert llamadas[1][1] == {"identidad": None}
