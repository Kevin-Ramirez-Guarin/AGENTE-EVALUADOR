"""Robustez del matching: si el LLM no nombró un requisito pero la HV (anonimizada) sí lo dice."""
from app.scoring import evaluar, mejor_vacante
from tests.agent.test_scoring import VACANTES, crit, perfil, vacante

FRONT = next(v for v in VACANTES if v.id == "frontend-react")
HV = ("Profesional de desarrollo frontend. Aplicaciones con React y TypeScript, JavaScript moderno, "
      "HTML y CSS semántico. Comunicación constante con diseño.")


def test_el_llm_no_nombro_javascript_pero_la_hv_si_lo_dice():
    p = perfil(tec=["React", "HTML/CSS"], anios=3, edu="profesional")
    sin_texto = evaluar(p, FRONT)
    con_texto = evaluar(p, FRONT, HV)
    assert not sin_texto.cumple_obligatorios and sin_texto.puntaje_total <= 40
    assert con_texto.cumple_obligatorios and "JavaScript" in crit(con_texto, "tecnico").cumplidos
    assert con_texto.puntaje_total > sin_texto.puntaje_total


def test_la_evidencia_es_un_fragmento_citado_de_la_hv():
    p = perfil(tec=["React", "HTML/CSS"], anios=3, edu="profesional")
    ev = crit(evaluar(p, FRONT, HV), "tecnico").evidencias
    citas = [e for e in ev if e.startswith("Mencionado en la hoja de vida: «")]
    assert len(citas) == 1 and "JavaScript moderno" in citas[0] and citas[0].endswith("»")


def test_el_fragmento_no_pasa_de_120_caracteres_y_conserva_tildes_del_original():
    largo = "Introducción " * 30 + "Estadística básica con R " + "relleno " * 40
    v = vacante(requisitos_obligatorios=["Estadística básica"])
    ev = crit(evaluar(perfil(), v, largo), "tecnico").evidencias[0]
    fragmento = ev.split("«", 1)[1].rstrip("»")
    assert len(fragmento) <= 120 and "Estadística básica" in fragmento


def test_aplica_limites_de_palabra_y_sinonimos_como_con_las_habilidades():
    v = vacante(requisitos_obligatorios=["Java", "SQL"])
    res = evaluar(perfil(), v, "Experiencia con JavaScript y PostgreSQL")
    c = crit(res, "tecnico")
    assert c.cumplidos == ["SQL"] and c.faltantes == ["Java"]  # JavaScript no cuenta como Java; PostgreSQL sí como SQL


def test_las_habilidades_del_perfil_tienen_prioridad_sobre_el_texto():
    p = perfil(tec=[("Python")])
    ev = crit(evaluar(p, vacante(), "Python en el texto"), "tecnico").evidencias
    assert ev == ["uso Python"]


def test_busca_tambien_las_blandas_y_los_deseables():
    v = vacante(deseables=["Docker"], blandas=["Trabajo en equipo"])
    res = evaluar(perfil(tec=["Python"]), v, "Contenedores con docker. Trabajo en equipo constante.")
    assert crit(res, "tecnico").faltantes == [] and crit(res, "blandas").cumplidos == ["Trabajo en equipo"]


def test_sin_texto_o_con_texto_vacio_el_resultado_no_cambia():
    p = perfil(tec=["Python"], anios=2)
    assert evaluar(p, vacante()) == evaluar(p, vacante(), None) == evaluar(p, vacante(), "")


def test_mejor_vacante_tambien_usa_el_texto():
    p = perfil(tec=["React", "HTML/CSS", "TypeScript"], anios=3, edu="profesional", idiomas=[("inglés", "B1")])
    assert mejor_vacante(p, VACANTES, "backend-jr") is None
    assert mejor_vacante(p, VACANTES, "backend-jr", HV) == "frontend-react"
