"""Plantillas de los correos al candidato (texto plano)."""
from datetime import datetime

FIRMA = "Equipo de Selección"


def correo_invitacion(nombre: str, vacante: str, inicio_iso: str, meet_link: str) -> tuple[str, str]:
    inicio = datetime.fromisoformat(inicio_iso)
    cuerpo = (
        f"Hola {nombre},\n\n"
        f"¡Qué gusto contarte que avanzaste en el proceso para {vacante}! "
        "Nos encantaría conocerte en una entrevista.\n\n"
        f"Fecha: {inicio:%d/%m/%Y} a las {inicio:%H:%M} (hora de Colombia)\n"
        f"Enlace de Google Meet: {meet_link}\n\n"
        "También te llegó la invitación de calendario. Si no puedes asistir, "
        "responde a este correo y buscamos otro horario.\n\n"
        f"Un saludo,\n{FIRMA}\n"
    )
    return f"Invitación a entrevista: {vacante}", cuerpo


def correo_no_continua(nombre: str, vacante: str, explicaciones: list[str]) -> tuple[str, str]:
    detalle = "\n".join(f"- {e}" for e in explicaciones)
    cuerpo = (
        f"Hola {nombre},\n\n"
        f"Gracias por postularte a {vacante} y por el tiempo que dedicaste. "
        "En esta ocasión no continuaremos con tu proceso.\n\n"
        f"Te contamos brevemente por qué:\n{detalle}\n\n"
        "Esta decisión la tomó una persona de nuestro equipo, apoyada por una herramienta "
        "de análisis. Si quieres que revisemos tu caso, responde a este correo pidiendo "
        "una revisión y con gusto lo haremos.\n\n"
        f"Te deseamos mucho éxito.\n{FIRMA}\n"
    )
    return f"Sobre tu postulación a {vacante}", cuerpo
