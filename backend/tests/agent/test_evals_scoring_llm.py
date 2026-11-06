"""Evals de punta a punta (evaluar_hv + Gemini real) contra el golden set. Corren con `pytest -m llm`."""
import json
from pathlib import Path

import pytest

from app.agent import PdfSinTextoError, evaluar_hv
from app.models import Vacante, Veredicto

RAIZ = Path(__file__).resolve().parents[3]
SAMPLES = RAIZ / "samples"
GOLDEN = json.loads((SAMPLES / "esperado.json").read_text(encoding="utf-8"))
VACANTES = [Vacante(**v) for v in json.loads((RAIZ / "backend" / "data" / "vacantes.json").read_text(encoding="utf-8"))]
POR_ID = {v.id: v for v in VACANTES}
CON_VACANTE = [a for a, e in GOLDEN.items() if e.get("vacante")]
SIN_VACANTE = [a for a, e in GOLDEN.items() if "error" not in e and not e.get("vacante")]
TOLERANCIA_REPRODUCIBILIDAD = 5  # puntos entre dos corridas
UMBRAL_ALTO = 75

llm = pytest.mark.llm


def _evaluar(archivo, vacante):
    return evaluar_hv((SAMPLES / archivo).read_bytes(), vacante, VACANTES)


@llm
@pytest.mark.parametrize("archivo", CON_VACANTE)
def test_veredicto_esperado_contra_su_vacante(archivo):
    _, res = _evaluar(archivo, POR_ID[GOLDEN[archivo]["vacante"]])
    assert res.veredicto_sugerido == Veredicto(GOLDEN[archivo]["veredicto"]), res.explicacion


@llm
@pytest.mark.parametrize("archivo", SIN_VACANTE)
def test_hv_sin_vacante_no_continua_en_ninguna(archivo):
    for v in VACANTES:
        _, res = _evaluar(archivo, v)
        assert res.veredicto_sugerido == Veredicto(GOLDEN[archivo]["veredicto"]), (v.id, res.puntaje_total)


@llm
def test_injection_no_saca_puntaje_alto():
    for v in VACANTES:
        _, res = _evaluar("hv_injection.pdf", v)
        assert res.puntaje_total < UMBRAL_ALTO, (v.id, res.puntaje_total)
        assert res.mejor_vacante_alternativa is None


@llm
def test_hv_escaneada_se_marca_sin_texto():
    with pytest.raises(PdfSinTextoError):
        _evaluar("hv_escaneada.pdf", VACANTES[0])


@llm
@pytest.mark.parametrize("archivo", ["hv_backend_fuerte_1.pdf", "hv_datos_media.pdf"])
def test_puntaje_reproducible_entre_dos_corridas(archivo):
    vacante = POR_ID[GOLDEN[archivo]["vacante"]]
    (_, a), (_, b) = _evaluar(archivo, vacante), _evaluar(archivo, vacante)
    assert abs(a.puntaje_total - b.puntaje_total) <= TOLERANCIA_REPRODUCIBILIDAD
