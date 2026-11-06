"""Prueba de humo: pide a Gemini un PerfilCandidato desde una HV sintética.

Uso (desde backend/): python -m scripts.smoke_gemini
"""
from app.llm import get_llm
from app.models import PerfilCandidato

HV_SINTETICA = """\
Perfil: desarrolladora backend con 2 años de experiencia.
Experiencia: Dev Python en Acme (2023-2025), APIs con FastAPI y PostgreSQL, control de versiones con Git.
Educación: Tecnóloga en Desarrollo de Software (SENA).
Idiomas: inglés B1.
Habilidades blandas: trabajo en equipo, aprendizaje rápido.
"""


def extraer_perfil(texto: str) -> PerfilCandidato:
    return get_llm().with_structured_output(PerfilCandidato).invoke(
        f"Extrae el perfil del candidato. Cita evidencia textual de la HV.\n\n{texto}"
    )


if __name__ == "__main__":
    print(extraer_perfil(HV_SINTETICA).model_dump_json(indent=2))
