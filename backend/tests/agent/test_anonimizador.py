"""Anonimizador determinístico: identidad, datos personales y neutralización de género."""
import pytest

from app.anonymizer import anonimizar, contiene_genero

ID = {"nombre": "Laura Camila Restrepo Gómez", "email": "laura@example.com"}


def test_reemplaza_el_nombre_sin_importar_mayusculas_ni_tildes():
    out = anonimizar("Referencia: LAURA restrepo gomez trabajó con camila.", ID)
    assert "[PERSONA]" in out
    for palabra in ("laura", "restrepo", "gomez", "camila"):
        assert palabra not in out.lower()


def test_el_nombre_exige_palabra_completa_y_minimo_3_letras():
    assert anonimizar("Analista de datos. Ana lidera.", {"nombre": "Ana", "email": ""}) == "Analista de datos. [PERSONA] lidera."
    assert anonimizar("Li gana", {"nombre": "Li Wei", "email": ""}) == "Li gana"


def test_nombre_compuesto_se_colapsa_en_una_sola_marca():
    assert anonimizar("Laura Camila Restrepo Gómez\nPerfil de ventas", ID).startswith("[PERSONA]\nPerfil")


def test_particulas_del_nombre_no_se_reemplazan_en_el_resto_del_texto():
    out = anonimizar("María del Pilar Gómez\nResponsable del área de datos", {"nombre": "María del Pilar Gómez", "email": ""})
    assert out == "[PERSONA]\nResponsable del área de datos"


def test_sin_identidad_no_reemplaza_nombres():
    assert "Laura" in anonimizar("Laura Restrepo es analista de datos.", None)


@pytest.mark.parametrize("original", ["laura.restrepo@example.com", "a_b+c@sub.dominio.co"])
def test_elimina_correos(original):
    out = anonimizar(f"Escríbeme a {original} para hablar de SQL.")
    assert original not in out and "@" not in out


@pytest.mark.parametrize("tel", ["300 111 2233", "3001112233", "+57 300 111 2233", "+573001112233", "(601) 234 5678", "300-111-2233"])
def test_elimina_telefonos_colombianos(tel):
    out = anonimizar(f"Celular {tel} disponible.")
    assert "111" not in out and "234" not in out and "[TELEFONO]" in out


@pytest.mark.parametrize("doc", ["Cédula 1.000.111.222", "C.C. 1000111222", "CC 52.123.456", "Documento de identidad: 1000111222"])
def test_elimina_cedula_y_documentos(doc):
    out = anonimizar(f"{doc}\nPython y SQL")
    assert not any(ch.isdigit() for ch in out) and "Python y SQL" in out


def test_elimina_urls():
    out = anonimizar("Perfil en https://linkedin.com/in/laura-r y github.com/laura\nlinkedin: /in/laura\nPython")
    assert "laura" not in out and "linkedin" not in out.lower() and "github" not in out.lower()
    assert "Python" in out


def test_no_toca_anios_de_experiencia_ni_rangos_de_fechas():
    texto = "Desarrollo con 3 años de experiencia. Soluciones Andinas (2022-2025). 2 años en Docker."
    assert anonimizar(texto) == texto


@pytest.mark.parametrize("edad", ["Edad: 25", "Edad 31 años", "25 años de edad", "Tengo 28 años."])
def test_elimina_la_edad(edad):
    out = anonimizar(f"{edad}\nPython con 3 años de experiencia")
    assert out == "Python con 3 años de experiencia"


@pytest.mark.parametrize("nacimiento", [
    "Fecha de nacimiento: 12/03/2000", "Fecha de nacimiento: 12 de marzo de 2000",
    "Nacido el 12 de marzo de 2000.", "Nacida el 12/03/2000",
])
def test_elimina_fecha_de_nacimiento(nacimiento):
    assert anonimizar(f"{nacimiento}\nGit y Docker") == "Git y Docker"


@pytest.mark.parametrize("frase", [
    "Nacida en Caracas, Venezuela.", "Nacido en Quibdó.", "Lugar de nacimiento: Quibdó",
    "Residente en Bogotá.", "Vivo en Cali.", "Ciudad: Medellín", "Dirección: Calle 45 # 12-30, Bogotá",
    "Domicilio: Carrera 7 # 45-10",
])
def test_elimina_origen_y_residencia(frase):
    assert anonimizar(f"{frase}\nPython") == "Python"


@pytest.mark.parametrize("frase", [
    "Estado civil: Soltera", "Estado civil: Unión libre", "Casado.", "Soltero",
    "Nacionalidad: Venezolana", "Soy colombiana", "De origen peruano.", "Venezolano",
])
def test_elimina_estado_civil_y_nacionalidad(frase):
    assert anonimizar(f"{frase}\nPython") == "Python"


def test_una_linea_solo_de_contacto_desaparece():
    assert anonimizar("laura@example.com | +57 300 111 2233 | Medellín\nPerfil") == "Perfil"


def test_en_una_linea_con_contacto_solo_se_borra_el_contacto():
    assert anonimizar("a@b.com | github.com/x | Python, SQL") == "Python, SQL"
    assert anonimizar("Email: a@b.com | Tel: 300 111 2233 | Caracas, Venezuela | Docker") == "Docker"
    assert anonimizar("Celular 300 111 2233 disponible.") == "Celular [TELEFONO] disponible."


@pytest.mark.parametrize("frase", [
    "F. nacimiento: 12/03/2000", "F. de nac.: 12/03/2000", "Fecha nac. 12-03-2000",
    "Fecha de nac: 12 de marzo de 2000", "f.nac: 12/03/2000",
])
def test_elimina_abreviaturas_de_fecha_de_nacimiento(frase):
    assert anonimizar(f"{frase}\nGit") == "Git"


@pytest.mark.parametrize("original,esperado", [
    ("Mujer con experiencia", "Persona con experiencia"),
    ("Soy hombre responsable", "Soy persona responsable"),
    ("Perfil femenino", "Perfil"),
    ("Perfil masculino", "Perfil"),
    ("Jefa de proyecto", "Responsable de proyecto"),
    ("El jefe de bodega", "Responsable de bodega"),
    ("Directora de proyectos", "Profesional de dirección de proyectos"),
    ("Director de proyectos", "Profesional de dirección de proyectos"),
    ("Profesora de matemáticas", "Profesional de docencia de matemáticas"),
    ("Profesor de matemáticas", "Profesional de docencia de matemáticas"),
    ("Presidenta del club", "Persona en la presidencia del club"),
    ("Presidente del club", "Persona en la presidencia del club"),
    ("Coordinadora de QA", "Profesional de coordinación de QA"),
    ("Coordinador de QA", "Profesional de coordinación de QA"),
    ("Gerenta de ventas", "Gerente de ventas"),
    ("Ellas lideraron", "lideraron"),
    ("Ellos lideraron", "lideraron"),
])
def test_neutraliza_mas_roles_y_pronombres(original, esperado):
    assert anonimizar(original) == esperado
    assert contiene_genero(original) != [] and contiene_genero(esperado) == []


def test_no_confunde_direccion_ni_profesional_con_roles_de_genero():
    texto = "Dirección de proyectos con enfoque profesional"
    assert anonimizar(texto) == texto


@pytest.mark.parametrize("texto", [
    "Colegio Colombiano de Ingenieros", "Cámara Colombiana de la Construcción", "Estudié en la Universidad Venezolana",
])
def test_gentilicio_dentro_de_una_institucion_no_se_borra(texto):
    assert anonimizar(texto) == texto


def test_lineas_de_datos_eliminadas_no_dejan_huecos_ni_separadores():
    assert anonimizar("Perfil\n\nEdad: 25 | Soltera\n\nPython  y   SQL") == "Perfil\nPython y SQL"


# ── neutralización de género ────────────────────────────────────────────────────
@pytest.mark.parametrize("original,esperado", [
    ("Desarrolladora backend", "Profesional de desarrollo backend"),
    ("Desarrollador backend", "Profesional de desarrollo backend"),
    ("Desarrollador/a backend", "Profesional de desarrollo backend"),
    ("Ingeniera de sistemas", "Profesional en ingeniería de sistemas"),
    ("Ingeniero de sistemas junior", "Profesional en ingeniería de sistemas junior"),
    ("Tecnóloga en Análisis de Software", "Título de tecnología en Análisis de Software"),
    ("Tecnólogo en Análisis de Software", "Título de tecnología en Análisis de Software"),
    ("Técnica en Sistemas", "Formación técnica en Sistemas"),
    ("Técnico en Sistemas", "Formación técnica en Sistemas"),
    ("egresada de la Universidad", "con título de la Universidad"),
    ("egresado de la Universidad", "con título de la Universidad"),
    ("Soy una desarrolladora apasionada por la tecnología", "Soy profesional de desarrollo con pasión por la tecnología"),
    ("Soy un desarrollador apasionado por la tecnología", "Soy profesional de desarrollo con pasión por la tecnología"),
    ("Ella lideró el equipo", "lideró el equipo"),
    ("Él lideró el equipo", "lideró el equipo"),
    ("La señora Gómez ingresó", "Gómez ingresó"),
    ("Sexo: Femenino\nPython", "Python"),
])
def test_neutraliza_genero(original, esperado):
    assert anonimizar(original) == esperado


def test_no_confunde_el_articulo_el_con_el_pronombre_el():
    texto = "Trabajé en el área de datos con el equipo"
    assert anonimizar(texto) == texto


def test_no_neutraliza_terminos_que_no_son_de_genero():
    texto = "Ingeniería de Sistemas, soporte técnico, pensamiento analítico, don de gentes"
    assert anonimizar(texto) == texto


@pytest.mark.parametrize("texto,nivel", [
    ("Tecnóloga en ADSO, SENA", "título de tecnología"),
    ("Técnica en Sistemas", "formación técnica"),
    ("Ingeniero de sistemas", "profesional"),
    ("Ingeniera de sistemas", "profesional"),
    ("Magíster en Analítica de Datos", "magíster"),
    ("Especialización en Estadística", "especialización"),
    ("Doctora en Matemáticas", "doctorado"),
])
def test_el_nivel_educativo_sigue_siendo_inferible(texto, nivel):
    assert nivel in anonimizar(texto).lower()


def test_contiene_genero_detecta_y_lo_anonimizado_queda_limpio():
    sucio = "Desarrolladora y técnico en sistemas, ella es ingeniera de datos, apasionado"
    assert len(contiene_genero(sucio)) >= 4
    assert contiene_genero(anonimizar(sucio)) == []
    assert contiene_genero("") == []


def test_es_deterministico_e_idempotente():
    texto = "Ingeniera de sistemas. Edad: 25. laura@example.com"
    una = anonimizar(texto, ID)
    assert una == anonimizar(texto, ID) == anonimizar(una, ID)


def test_texto_vacio():
    assert anonimizar("", ID) == ""
