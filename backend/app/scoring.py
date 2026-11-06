"""Reglas de negocio determinísticas (PLAN.md §5). El LLM extrae; aquí Python calcula."""
import re
import unicodedata

from app.models import (
    CriterioDetalle,
    Habilidad,
    PerfilCandidato,
    ResultadoEvaluacion,
    Vacante,
    Veredicto,
)

PESO_OBLIGATORIOS = 0.7
TOPE_KNOCKOUT = 40.0
UMBRAL_ENTREVISTA = 75.0
UMBRAL_REVISION = 55.0
ORDEN_EDUCACION = ["bachiller", "tecnico", "tecnologo", "profesional", "posgrado"]
MCER = ["A1", "A2", "B1", "B2", "C1", "C2"]
NIVEL_NATIVO = len(MCER) - 1

# ponytail: sinónimos a mano para unos pocos términos del catálogo; si crecen las vacantes,
# pasarlos a vacantes.json o a embeddings. Fuera de este diccionario solo vale la coincidencia literal.
SINONIMOS = {
    "sql": ("postgresql", "mysql", "sqlite", "sql server"),
    "javascript": ("js", "node.js", "nodejs"),
    "estadistica basica": ("estadistica",),
    "excel avanzado": ("tablas dinamicas",),
    "atencion al cliente": ("servicio al cliente", "soporte al cliente"),
    "casos de prueba": ("test cases", "pruebas funcionales"),
    "reporte de bugs": ("reporte de errores", "bug reports"),
    "testing": ("pytest", "unittest", "pruebas unitarias"),
    "html/css": ("html", "css"),
}


def _norm(s: str) -> str:
    sin_tildes = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sin_tildes).strip().lower()


def _aparece(termino: str, texto: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(termino)}(?!\w)", texto) is not None


def _alternativas(requisito: str) -> list[str]:
    r = _norm(requisito)
    base = [r] if r in SINONIMOS else [a.strip() for a in r.split("/") if a.strip()]
    return base + [s for a in base for s in SINONIMOS.get(a, ())]


def _evidencia_de(requisito: str, habilidades: list[Habilidad]) -> str | None:
    """Evidencia de la primera habilidad que cubre el requisito, o None si no lo cubre."""
    alternativas = _alternativas(requisito)
    for h in habilidades:
        texto = _norm(f"{h.nombre} {h.evidencia}")
        if any(_aparece(a, texto) for a in alternativas):
            return h.evidencia or h.nombre
    return None


def _cubrir(requisitos: list[str], habilidades: list[Habilidad]):
    cumplidos, faltantes, evidencias = [], [], []
    for r in requisitos:
        ev = _evidencia_de(r, habilidades)
        if ev is None:
            faltantes.append(r)
        else:
            cumplidos.append(r)
            if ev not in evidencias:
                evidencias.append(ev)
    return cumplidos, faltantes, evidencias


def _ratio(cumplidos: list, total: list) -> float:
    return len(cumplidos) / len(total) if total else 1.0


def _lista(items: list[str]) -> str:
    return ", ".join(items)


def _nivel_mcer(nivel: str) -> int:
    n = _norm(nivel)
    if "nativ" in n:
        return NIVEL_NATIVO
    m = re.search(r"\b([abc][12])\b", n)
    return MCER.index(m.group(1).upper()) if m else -1


def _detalle(nombre, ratio, peso, cumplidos, faltantes, evidencias, nota) -> CriterioDetalle:
    return CriterioDetalle(criterio=nombre, puntaje=round(ratio * 100, 1), peso=peso, cumplidos=cumplidos,
                           faltantes=faltantes, evidencias=evidencias, nota=nota)


def _tecnico(perfil, vacante):
    oc, of, oe = _cubrir(vacante.requisitos_obligatorios, perfil.habilidades_tecnicas)
    dc, df, de = _cubrir(vacante.deseables, perfil.habilidades_tecnicas)
    ratio = PESO_OBLIGATORIOS * _ratio(oc, vacante.requisitos_obligatorios) \
        + (1 - PESO_OBLIGATORIOS) * _ratio(dc, vacante.deseables)
    if of:
        nota = f"Para este cargo son imprescindibles: {_lista(of)}. No los vimos en tu hoja de vida; si los tienes, agrégalos con un ejemplo."
    elif df:
        nota = f"Cumples todo lo imprescindible. Reforzar {_lista(df)} te ayudaría a destacar."
    else:
        nota = "Cumples los requisitos técnicos imprescindibles y los deseables, con evidencia en tu hoja de vida."
    return _detalle("tecnico", ratio, vacante.pesos.tecnico, oc + dc, of + df, oe + de, nota), not of


def _experiencia(perfil, vacante):
    minimo = vacante.experiencia_min_anios
    ratio = 1.0 if minimo <= 0 else min(1.0, perfil.anios_experiencia / minimo)
    texto = f"{perfil.anios_experiencia:g} años (mínimo {minimo:g})"
    if ratio >= 1:
        return _detalle("experiencia", ratio, vacante.pesos.experiencia, [texto], [], [],
                        "Tu experiencia alcanza lo que pide el cargo.")
    return _detalle("experiencia", ratio, vacante.pesos.experiencia, [], [texto], [],
                    "Tu experiencia está por debajo de lo que pide el cargo, pero tu perfil puede seguir creciendo.")


def _blandas(perfil, vacante):
    c, f, e = _cubrir(vacante.blandas, perfil.habilidades_blandas)
    nota = (f"Valoraríamos ver evidencia de: {_lista(f)}." if f
            else "Tu hoja de vida muestra las habilidades blandas que busca el cargo.")
    return _detalle("blandas", _ratio(c, vacante.blandas), vacante.pesos.blandas, c, f, e, nota)


def _educacion(perfil, vacante):
    tiene, pide = ORDEN_EDUCACION.index(perfil.nivel_educativo), ORDEN_EDUCACION.index(vacante.nivel_educativo_min)
    ratio = 1.0 if tiene >= pide else (tiene + 1) / (pide + 1)
    etiqueta = f"{perfil.nivel_educativo} (mínimo {vacante.nivel_educativo_min})"
    if ratio >= 1:
        return _detalle("educacion", ratio, vacante.pesos.educacion, [etiqueta], [], [], "Tu formación cumple con el nivel pedido.")
    return _detalle("educacion", ratio, vacante.pesos.educacion, [], [etiqueta], [],
                    "El cargo pide un nivel de formación mayor; la experiencia y los cursos también cuentan para el equipo.")


def _idiomas(perfil, vacante):
    tiene = {_norm(i.idioma): _nivel_mcer(i.nivel) for i in perfil.idiomas}
    cumplidos, faltantes, ratios = [], [], []
    for req in vacante.idiomas:
        pide, nivel = _nivel_mcer(req.nivel), tiene.get(_norm(req.idioma), -1)
        etiqueta = f"{req.idioma} {req.nivel}"
        (cumplidos if nivel >= pide else faltantes).append(etiqueta)
        ratios.append(1.0 if nivel >= pide else (nivel + 1) / (pide + 1))
    ratio = sum(ratios) / len(ratios) if ratios else 1.0
    nota = (f"Para este cargo se pide: {_lista(faltantes)}. Si ya tienes ese nivel, indícalo en tu hoja de vida."
            if faltantes else "Cumples con los idiomas que pide el cargo.")
    return _detalle("idiomas", ratio, vacante.pesos.idiomas, cumplidos, faltantes, [], nota)


def _veredicto(total: float) -> Veredicto:
    if total >= UMBRAL_ENTREVISTA:
        return Veredicto.ENTREVISTA
    return Veredicto.REVISION_HUMANA if total >= UMBRAL_REVISION else Veredicto.NO_CONTINUA


def _explicacion(vacante, total, cumple, faltantes, veredicto) -> str:
    oblig = ("Cumple todos los requisitos imprescindibles." if cumple
             else f"Faltan requisitos imprescindibles: {_lista(faltantes)}.")
    accion = {Veredicto.ENTREVISTA: "se sugiere entrevista",
              Veredicto.REVISION_HUMANA: "se sugiere revisión humana",
              Veredicto.NO_CONTINUA: "se sugiere no continuar por ahora"}[veredicto]
    return f"Puntaje {total:g} sobre 100 para {vacante.titulo}. {oblig} Con esto {accion}, sujeto a la decisión de una persona."


def evaluar(perfil: PerfilCandidato, vacante: Vacante) -> ResultadoEvaluacion:
    tecnico, cumple = _tecnico(perfil, vacante)
    criterios = [tecnico, _experiencia(perfil, vacante), _blandas(perfil, vacante),
                 _educacion(perfil, vacante), _idiomas(perfil, vacante)]
    total = round(sum(c.puntaje * c.peso for c in criterios), 1)
    if not cumple:
        total = min(total, TOPE_KNOCKOUT)
    veredicto = _veredicto(total)
    faltan_obligatorios = [r for r in vacante.requisitos_obligatorios if r in tecnico.faltantes]
    return ResultadoEvaluacion(
        puntaje_total=total,
        puntajes_por_criterio={c.criterio: c.puntaje for c in criterios},
        veredicto_sugerido=veredicto,
        cumple_obligatorios=cumple,
        explicacion=_explicacion(vacante, total, cumple, faltan_obligatorios, veredicto),
        criterios=criterios,
    )


def mejor_vacante(perfil: PerfilCandidato, vacantes: list[Vacante], actual_id: str) -> str | None:
    """Id de otra vacante con puntaje >= 75 y mayor que el de la actual; None si no hay."""
    puntajes = {v.id: evaluar(perfil, v).puntaje_total for v in vacantes}
    actual = puntajes.get(actual_id, -1.0)
    otras = {i: p for i, p in puntajes.items() if i != actual_id and p >= UMBRAL_ENTREVISTA and p > actual}
    return max(otras, key=otras.get) if otras else None
