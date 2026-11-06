"""Costura con el agente. El track IA conecta aquí el evaluador real sin tocar las rutas."""
from collections.abc import Callable

from app.models import PerfilCandidato, ResultadoEvaluacion, Vacante, Veredicto

Evaluador = Callable[[bytes, Vacante], tuple[PerfilCandidato, ResultadoEvaluacion]]


def evaluador_falso(pdf_bytes: bytes, vacante: Vacante) -> tuple[PerfilCandidato, ResultadoEvaluacion]:
    """Determinístico: el puntaje (50-99) depende solo de los bytes del PDF."""
    puntaje = 50 + sum(pdf_bytes) % 50
    veredicto = (Veredicto.ENTREVISTA if puntaje >= 75
                 else Veredicto.REVISION_HUMANA if puntaje >= 55
                 else Veredicto.NO_CONTINUA)
    perfil = PerfilCandidato(
        habilidades_tecnicas=[],
        habilidades_blandas=[],
        anios_experiencia=1,
        nivel_educativo="tecnologo",
        idiomas=[],
        fortalezas=["Evaluación simulada"],
        debilidades=[],
        resumen="Perfil de prueba generado por el evaluador falso.",
    )
    resultado = ResultadoEvaluacion(
        puntaje_total=puntaje,
        puntajes_por_criterio={k: float(puntaje) for k in vacante.pesos.model_dump()},
        veredicto_sugerido=veredicto,
        cumple_obligatorios=puntaje >= 55,
        explicacion="Resultado simulado, no proviene del agente real.",
    )
    return perfil, resultado


def get_evaluador() -> Evaluador:
    return evaluador_falso
