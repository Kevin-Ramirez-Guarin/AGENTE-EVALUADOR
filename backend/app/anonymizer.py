"""Anonimizador determinístico, sin LLM (PLAN.md §7).

El LLM nunca debe recibir identidad ni pistas de género, edad u origen: aquí se eliminan o
neutralizan antes de `extraer_perfil`. Mismo texto + misma identidad => misma salida.
"""
import re
import unicodedata

PERSONA = "[PERSONA]"
MIN_LETRAS_NOMBRE = 3
PARTICULAS = frozenset({"del", "los", "las", "van", "von", "der", "den", "san"})  # no son "el nombre"


def plegar(texto: str) -> str:
    """Minúsculas y sin tildes, conservando la longitud (así los índices valen sobre el original)."""
    return "".join(unicodedata.normalize("NFD", c)[0] for c in texto).lower()


def _reemplazar(patron: re.Pattern, repl: str, texto: str, capitalizar: bool = False) -> str:
    """Busca en la versión plegada y sustituye sobre el original (tildes y mayúsculas intactas)."""
    partes, pos = [], 0
    for m in patron.finditer(plegar(texto)):
        nuevo = m.expand(repl)
        if capitalizar and texto[m.start()].isupper():
            nuevo = nuevo[:1].upper() + nuevo[1:]
        partes += [texto[pos:m.start()], nuevo]
        pos = m.end()
    return "".join(partes) + texto[pos:]


def _c(patron: str, flags: int = 0) -> re.Pattern:
    return re.compile(patron, flags)


_DIA = r"\d{1,2}(?:[/.-]\d{1,2}[/.-]\d{2,4}|\s+de\s+[a-z]+\s+(?:de\s+)?\d{4})"
_FECHA_NAC = r"(?:fecha|f\.?)[ \t]*(?:de[ \t]+)?nac(?:imiento|\.)?"  # "Fecha de nacimiento", "F. nacimiento", "F. de nac."
_ETIQUETAS = (r"(?:lugar\s+de\s+(?:nacimiento|residencia)|direccion|domicilio|ciudad(?:\s+de\s+residencia)?|residencia|"
              r"ubicacion|nacionalidad|estado\s+civil|sexo|genero|edad)")
# ponytail: lista finita de gentilicios; uno que no esté aquí pasa (se mitiga con la etiqueta "Nacionalidad:").
_GENTILICIO = (r"(?:(?:colombian|venezolan|ecuatorian|peruan|mexican|argentin|chilen|brasilen|cuban|dominican|"
               r"haitian|nigerian)[oa]|ghanes(?:a)?|estadounidens[ea])")

# (patrón sobre texto plegado, reemplazo). El orden importa: contacto antes que documentos.
DATOS = [(_c(p), r) for p, r in [
    (r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", "[CORREO]"),
    (r"(?:https?://|www\.)\S+|\b(?:linkedin|github|gitlab|behance)\.com\S*|\b(?:linkedin|github|gitlab)\s*:\s*\S+", "[URL]"),
    (r"(?<!\d)(?:\+\s?\d{1,3}[\s.-]?|57[\s.-]?)?\(?(?:3\d{2}|60\d)\)?[\s.-]?\d{3}[\s.-]?\d{4}(?!\d)", "[TELEFONO]"),
    (r"(?<!\d)\d{3}[\s.-]\d{4}(?!\d)", "[TELEFONO]"),
    (r"\b(?:c\.?\s?c\.?|cedula(?:\s+de\s+ciudadania)?|documento(?:\s+de\s+identidad)?|nit|pasaporte)"
     r"[ \t]*(?:no\.?|numero|n[°º.]|#)?[ \t]*[:.]?[ \t]*\d[\d., ]{4,14}\d", "[DOCUMENTO]"),
    (r"(?<![\d.])\d{1,3}(?:\.\d{3}){2,3}(?![\d.])|(?<![\d.,-])\d{8,10}(?![\d-])", "[DOCUMENTO]"),
    (rf"\b{_FECHA_NAC}[ \t]*:?[ \t]*{_DIA}\.?", ""),
    (rf"\bnacid[oa](?:/a)?\s+el\s+{_DIA}\.?", ""),
    (rf"\b{_ETIQUETAS}[ \t]*:[ \t]*[^\n|;]+", ""),
    (r"\b\d{1,2}[ \t]+anos[ \t]+de[ \t]+edad\.?", ""),
    (r"\bedad[ \t]*\d{1,2}(?:[ \t]*anos)?\.?", ""),
    (r"\btengo[ \t]+\d{1,2}[ \t]+anos(?![ \t]+de[ \t]+experiencia)\.?", ""),
    (r"\b(?:nacid[oa](?:/a)?|residente|reside|residenciad[oa]|vivo|vive|domiciliad[oa])\s+en\s+[^.\n;|]+\.?", ""),
    (r"\b(?:calle|carrera|cra|cr|kra|avenida|av|diagonal|transversal|tv)\.?\s+\d+[^\n|;]*", ""),
    # solo en contexto de origen ("soy colombiana", "de origen peruano") o sola en su línea; no dentro de "Colegio Colombiano"
    (rf"\b(?:soy|ciudadan[oa]|de\s+nacionalidad|de\s+origen)\s+{_GENTILICIO}\b\.?|(?m:^)[ \t]*{_GENTILICIO}[ \t]*\.?[ \t]*(?m:$)", ""),
    (r"\b(?:solter|casad|divorciad|viud)[oa](?:/a)?\b\.?|\bunion\s+libre\b\.?", ""),
    (r"\b(?:madre|padre)\s+(?:cabeza\s+de\s+hogar|soltera?|de\s+familia)\b\.?", ""),
    (r"(?:\b(?:la|el)\s+)?\b(?:senora|senor|senorita|dona|sra|sr|srta)\b\.?", ""),
]]

_ART = r"(?:\b(?:un|una|el|la)\s+)?"
_F = r"(?:/ora|/a|a)?"  # desarrollador / desarrolladora / desarrollador/a / desarrollador/ora


# "experiencia técnica en Docker": tras estos sustantivos "técnica" es adjetivo, no el rol de la persona (y la forma
# neutra "formación técnica en" tampoco debe volver a reemplazarse).
_NO_ADJETIVO = "".join(rf"(?<!{n} )" for n in (
    "formacion", "experiencia", "habilidad", "capacidad", "base", "perfil", "conocimiento", "competencia", "aptitud",
    "destreza", "solucion", "asistencia", "gestion", "documentacion"))


def _rol(raiz: str) -> str:
    return rf"{_ART}{raiz}{_F}\b"


# ponytail: lista finita y hecha a mano de roles y adjetivos en femenino/masculino -> forma neutra que conserva el
# significado para el matching. Lo que no esté aquí pasa sin neutralizar; ampliar al detectar nuevos casos.
GENERO = [(_c(p), r) for p, r in [
    (rf"{_ART}ingenier[oa](?:/a)?\s+(de|en)\b", r"profesional en ingeniería \1"),
    (rf"{_ART}ingenier[oa](?:/a)?\b", "profesional de ingeniería"),
    (rf"{_ART}{_NO_ADJETIVO}tecnolog[oa](?:/a)?\b", "título de tecnología"),
    (rf"{_ART}{_NO_ADJETIVO}tecnic[oa](?:/a)?\s+profesional\b", "formación técnica profesional"),
    (rf"{_ART}{_NO_ADJETIVO}tecnic[oa](?:/a)?\s+en\b", "formación técnica en"),
    (r"\b(?:un|una|el|la)\s+tecnic[oa](?:/a)?\b", "profesional técnico"),  # sin artículo: "soporte técnico" no es persona
    (_rol("desarrollador"), "profesional de desarrollo"),
    (_rol("programador"), "profesional de programación"),
    (_rol("disenador"), "profesional de diseño"),
    (_rol("administrador"), "profesional de administración"),
    (_rol("contador"), "profesional de contaduría"),
    (_rol("director"), "profesional de dirección"),
    (_rol("profesor"), "profesional de docencia"),
    (_rol("coordinador"), "profesional de coordinación"),
    (rf"{_ART}jef[ae](?:/a)?\b", "responsable"),
    (rf"{_ART}gerenta\b", "gerente"),
    (rf"{_ART}president[ae]\b", "persona en la presidencia"),
    (r"\b(?:mujer|hombre)(?![\w-])", "persona"),
    (r"\b(?:femenin|masculin)[oa]\b", ""),
    (rf"{_ART}licenciad[oa](?:/a)?\b", "título de licenciatura"),
    (rf"{_ART}doctor(?:a)?(?:/a)?\s+en\b", "título de doctorado en"),
    (rf"{_ART}(?:egresad|graduad|titulad)[oa](?:/a)?\b", "con título"),
    (rf"{_ART}candidat[oa](?:/a)?\b", "persona candidata"),
    (r"\bapasionad[oa](?:/a)?\b", "con pasión"),
    (r"\bmotivad[oa](?:/a)?\b", "con motivación"),
    (r"\bcomprometid[oa](?:/a)?\b", "con compromiso"),
    (r"\bproactiv[oa](?:/a)?\b", "con proactividad"),
    (r"\borientad[oa](?:/a)?\s+a\b", "con orientación a"),
    (r"\binteresad[oa](?:/a)?\s+en\b", "con interés en"),
]]
PRONOMBRE = _c(r"\b(?:ellas|ellos|ella|él)\b", re.IGNORECASE)  # sobre el original: "el" (artículo) no lleva tilde
_COLAPSO_PERSONA = _c(r"\[PERSONA\](?:[ \t]+(?:de|del|la|las|los|y|e))*(?:[ \t]+\[PERSONA\])+")


def _frase_a_regex(frase: str) -> str:
    palabras = [r"(?:de|en)" if w == "\\1" else re.escape(w) for w in plegar(frase).split()]
    return r"\s+".join(palabras)


# Formas neutras que produce el propio anonimizador ("formación técnica en"): no cuentan como género.
_NEUTRAS = _c("|".join(_frase_a_regex(r) for _, r in GENERO if r))


def contiene_genero(texto: str) -> list[str]:
    """Fragmentos con marca de género de la lista (para pruebas y evals); ignora las formas neutras."""
    plano = _NEUTRAS.sub(lambda m: " " * len(m.group()), plegar(texto))
    hallados = [m.group() for patron, _ in GENERO for m in patron.finditer(plano)]
    return hallados + [m.group() for m in PRONOMBRE.finditer(texto)]


def _palabras_nombre(identidad: dict | None) -> list[str]:
    nombre = (identidad or {}).get("nombre") or ""
    palabras = re.findall(r"\w+", plegar(nombre))
    return sorted({p for p in palabras if len(p) >= MIN_LETRAS_NOMBRE and p not in PARTICULAS})


# ponytail: lista finita de ciudades y países para quitar el lugar suelto de una línea de contacto
# ("correo | tel | Caracas, Venezuela"); un lugar fuera de la lista sobrevive. Ampliar al detectarlo.
_PALABRAS_LUGAR = frozenset(
    "bogota medellin cali barranquilla cartagena bucaramanga pereira manizales cucuta ibague santa marta villavicencio "
    "pasto monteria neiva armenia popayan quibdo valledupar sincelejo tunja riohacha florencia yopal soacha bello "
    "envigado itagui palmira caracas maracaibo valencia venezuela colombia ecuador peru mexico argentina chile d c".split())
_ETIQUETAS_CONTACTO = frozenset("tel telefono celular cel movil whatsapp correo email e-mail contacto linkedin github".split())
_MARCAS = re.compile(r"\[(?:CORREO|TELEFONO|DOCUMENTO|URL)\]")


def _solo_contacto(segmento: str) -> bool:
    """Segmento de una línea de contacto: solo marcas, etiquetas ("Tel:") o lugares sueltos."""
    palabras = [p for p in re.split(r"[\s,.:;]+", plegar(_MARCAS.sub(" ", segmento))) if p]
    return all(p in _ETIQUETAS_CONTACTO or p in _PALABRAS_LUGAR for p in palabras)


def _limpiar(texto: str) -> str:
    """Espacios normalizados, sin líneas vacías; en líneas con contacto se quita solo el contacto."""
    lineas = []
    for linea in texto.splitlines():
        partes = [re.sub(r"[ \t]+", " ", p).strip() for p in linea.split("|")]
        if _MARCAS.search(linea):
            partes = [p for p in partes if not _solo_contacto(p)]
        linea = " | ".join(p for p in partes if p)
        if linea:
            lineas.append(linea)
    return "\n".join(lineas)


def anonimizar(texto: str, identidad: dict | None = None) -> str:
    for patron, repl in DATOS:
        texto = _reemplazar(patron, repl, texto)
    palabras = _palabras_nombre(identidad)
    if palabras:
        texto = _reemplazar(_c(rf"(?<!\w)(?:{'|'.join(map(re.escape, palabras))})(?!\w)"), PERSONA, texto)
        texto = _COLAPSO_PERSONA.sub(PERSONA, texto)
    for patron, repl in GENERO:
        texto = _reemplazar(patron, repl, texto, capitalizar=True)
    return _limpiar(PRONOMBRE.sub("", texto))
