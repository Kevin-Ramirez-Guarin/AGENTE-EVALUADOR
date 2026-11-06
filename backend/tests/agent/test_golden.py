"""El golden set (samples/) cubre los tres veredictos y está en sincronía con generar_hv.py. Sin LLM."""
import json
from pathlib import Path

from app.agent import extraer_texto_pdf
from app.anonymizer import anonimizar
from app.models import Vacante, Veredicto
from app.scoring import evaluar
from scripts.generar_hv import construir_esperado
from tests.agent.test_scoring import hab, perfil

RAIZ = Path(__file__).resolve().parents[3]
GOLDEN = json.loads((RAIZ / "samples" / "esperado.json").read_text(encoding="utf-8"))
VACANTES = {v["id"]: Vacante(**v) for v in json.loads((RAIZ / "backend" / "data" / "vacantes.json").read_text(encoding="utf-8"))}
ARCHIVO = "hv_qa_limite.pdf"


def test_esperado_json_coincide_con_lo_que_genera_el_script():
    assert GOLDEN == construir_esperado()


def test_el_golden_cubre_los_tres_veredictos():
    assert {e["veredicto"] for e in GOLDEN.values() if e["veredicto"]} == {v.value for v in Veredicto}


def test_hv_qa_limite_cumple_los_obligatorios_pero_cae_en_revision_humana():
    esperado = GOLDEN[ARCHIVO]
    texto = anonimizar(extraer_texto_pdf((RAIZ / "samples" / ARCHIVO).read_bytes()),
                       {"nombre": esperado["nombre"], "email": esperado["correo"]})
    # lo que extraería un LLM fiel a la HV (sin deseables ni "Rigurosidad")
    p = perfil(tec=[hab("Casos de prueba", "Diseño de casos de prueba manuales"), hab("Reporte de bugs", "reporte de bugs")],
               blandas=["Comunicación"], anios=0.5, edu=esperado["nivel_educativo"], idiomas=[("inglés", "A1")])
    for t in (None, texto):  # con o sin el texto de respaldo
        res = evaluar(p, VACANTES[esperado["vacante"]], t)
        assert res.cumple_obligatorios
        assert 55 <= res.puntaje_total < 75
        assert res.veredicto_sugerido == Veredicto.REVISION_HUMANA == Veredicto(esperado["veredicto"])


def test_los_obligatorios_de_la_hv_qa_limite_estan_en_su_texto_aunque_el_perfil_venga_vacio():
    esperado = GOLDEN[ARCHIVO]
    texto = anonimizar(extraer_texto_pdf((RAIZ / "samples" / ARCHIVO).read_bytes()))
    res = evaluar(perfil(anios=0.5, edu="tecnico"), VACANTES[esperado["vacante"]], texto)
    assert res.cumple_obligatorios
