"""Prueba de ceguera determinística: la evidencia central del informe de sesgo.

Variantes de una misma HV que cambian SOLO nombre, género gramatical, origen, edad y estado civil.
Con su `identidad`, `anonimizar` debe devolver exactamente el mismo texto: el LLM recibe una entrada idéntica.
"""
import pytest

from app.agent import extraer_texto_pdf
from app.anonymizer import anonimizar, contiene_genero
from scripts.variantes_hv import VARIANTES, identidad_de, pdf_de, texto_hv


def test_hay_al_menos_seis_variantes_que_si_difieren_en_el_texto_crudo():
    assert len(VARIANTES) >= 6
    assert len({texto_hv(v) for v in VARIANTES}) == len(VARIANTES)
    assert {v["genero"] for v in VARIANTES} == {"f", "m"}


def test_las_variantes_incluyen_los_casos_dificiles():
    crudos = [texto_hv(v) for v in VARIANTES]
    for marca in ("F. nacimiento", "F. de nac.", "Fecha nac.", "mujer", "hombre", "Jefa", "Jefe"):
        assert any(marca in t for t in crudos), marca
    # el contacto comparte línea con habilidades y eso debe sobrevivir
    assert all(any("@" in l and "Python, SQL" in l for l in t.splitlines()) for t in crudos)
    assert all("Python, SQL" in anonimizar(t, identidad_de(v)).splitlines() for t, v in zip(crudos, VARIANTES))


def test_anonimizar_devuelve_exactamente_el_mismo_texto_para_todas_las_variantes():
    salidas = {anonimizar(texto_hv(v), identidad_de(v)) for v in VARIANTES}
    assert len(salidas) == 1, "\n---\n".join(salidas)


def test_la_misma_igualdad_vale_tras_el_ciclo_pdf():
    salidas = {anonimizar(extraer_texto_pdf(pdf_de(v)), identidad_de(v)) for v in VARIANTES}
    assert len(salidas) == 1, "\n---\n".join(salidas)


@pytest.mark.parametrize("variante", VARIANTES, ids=lambda v: v["nombre"])
def test_lo_anonimizado_no_filtra_identidad_ni_genero_y_conserva_lo_evaluable(variante):
    out = anonimizar(texto_hv(variante), identidad_de(variante)).lower()
    assert contiene_genero(out) == []
    for dato in (*variante["nombre"].split(), variante["origen"], variante["email"], variante["tel"], str(variante["edad"])):
        assert dato.lower() not in out
    for evaluable in ("Python", "SQL", "Git", "FastAPI", "Docker", "7 meses de experiencia", "Inglés A1",
                      "formación técnica en sistemas"):
        assert evaluable.lower() in out


def test_sin_identidad_el_nombre_no_se_infiere():
    v = VARIANTES[0]
    assert v["nombre"].split()[0] in anonimizar(texto_hv(v), None)
