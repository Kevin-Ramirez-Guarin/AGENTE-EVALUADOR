"""Rutas de postulaciones y evaluaciones (docs/api.md)."""
import json
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import NoReturn

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import and_, case, or_, update
from sqlmodel import Session, select

from app.agent import PdfInvalidoError, PdfSinTextoError, extraer_texto_pdf
from app.correos import correo_invitacion, correo_no_continua
from app.db import (MINUTOS_EVALUACION_ATASCADA, Auditoria, Candidato, Evaluacion,
                    Postulacion, get_engine, get_session)
from app.evaluador import Evaluador, get_evaluador
from app.google_apis import siguiente_horario
from app.models import Veredicto
from app.notificador import get_notificador

router = APIRouter()

MAX_PDF_BYTES = 5 * 1024 * 1024
EMAIL_RE = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"  # patrón simple; evita sumar email-validator
ERRORES_PDF = {
    PdfInvalidoError: (415, "El archivo no es un PDF válido"),
    PdfSinTextoError: (422, "No pudimos leer texto en tu PDF; ¿es un escaneo? "
                            "Súbelo con texto seleccionable"),
}
UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"


def get_uploads_dir() -> Path:
    # Lectura perezosa: pruebas y e2e pueden cambiar la variable sin reimportar.
    return Path(os.environ["UPLOADS_DIR"]) if os.environ.get("UPLOADS_DIR") else UPLOADS_DIR


def _auditar(session: Session, evento: str, evaluacion_id: int | None, detalle: dict) -> None:
    session.add(Auditoria(evento=evento, evaluacion_id=evaluacion_id,
                          detalle=json.dumps(detalle, ensure_ascii=False)))


def _rechazar(session: Session, status: int, detail: str, vacante_id: str) -> NoReturn:
    """Audita el rechazo (sin PDF ni datos personales) y responde con el error."""
    _auditar(session, "postulacion_rechazada", None,
             {"status": status, "motivo": detail, "vacante_id": vacante_id})
    session.commit()
    raise HTTPException(status, detail)


def _persistir(session: Session, uploads: Path, contenido: bytes, vacante_id: str,
               nombre: str, email: str) -> Evaluacion:
    """Escribe el PDF y las filas (evaluación en_evaluacion); si algo falla, borra el PDF y hace rollback."""
    uploads.mkdir(parents=True, exist_ok=True)
    # El nombre en disco es un UUID; el nombre del cliente nunca se usa.
    destino = uploads / f"{uuid.uuid4()}.pdf"
    try:
        destino.write_bytes(contenido)
        candidato = Candidato(nombre=nombre, email=email)
        session.add(candidato)
        session.flush()
        post = Postulacion(candidato_id=candidato.id, vacante_id=vacante_id,
                           pdf_path=destino.name, consentimiento_at=datetime.now(timezone.utc))
        session.add(post)
        session.flush()
        ev = Evaluacion(postulacion_id=post.id)
        session.add(ev)
        session.commit()
        return ev
    except Exception:
        session.rollback()
        destino.unlink(missing_ok=True)
        raise


def _marcar_error(session: Session, ev: Evaluacion, vacante_id: str, exc: Exception) -> None:
    # Solo el tipo de la excepción: sin trazas ni datos personales.
    ev.estado, ev.error = "error_evaluacion", f"Falló la evaluación ({type(exc).__name__})"
    _auditar(session, "evaluacion_fallida", ev.id,
             {"vacante_id": vacante_id, "error": type(exc).__name__})
    session.add(ev)
    session.commit()


def evaluar_en_segundo_plano(evaluacion_id: int, evaluador: Evaluador, uploads: Path) -> None:
    """Corre fuera de la petición, con su propia sesión; nunca lanza (el fallo queda en la fila)."""
    with Session(get_engine()) as session:
        ev = session.get(Evaluacion, evaluacion_id)
        post = session.get(Postulacion, ev.postulacion_id)
        cand = session.get(Candidato, post.candidato_id)
        vacante_id = post.vacante_id
        try:
            vacante = next(v for v in _vacantes() if v.id == vacante_id)
            pdf = (uploads / post.pdf_path).read_bytes()
            perfil, resultado = evaluador(
                pdf, vacante, identidad={"nombre": cand.nombre, "email": cand.email})
            ev.puntaje_total = resultado.puntaje_total
            ev.perfil = perfil.model_dump(mode="json")
            ev.resultado = resultado.model_dump(mode="json")
            ev.veredicto_ia = resultado.veredicto_sugerido.value
            ev.estado, ev.error = "pendiente_revision", None
            _auditar(session, "evaluacion_creada", ev.id,
                     {"vacante_id": vacante_id, "veredicto_sugerido": ev.veredicto_ia,
                      "puntaje_total": ev.puntaje_total,
                      "consentimiento_at": post.consentimiento_at.isoformat()})
            session.add(ev)
            session.commit()
            return
        except Exception as exc:
            session.rollback()
            error = exc
    # Sesión nueva: la anterior pudo quedar inservible (p. ej. falló el commit del resultado).
    with Session(get_engine()) as session:
        _marcar_error(session, session.get(Evaluacion, evaluacion_id), vacante_id, error)


# Función síncrona: FastAPI la corre en un hilo, así el I/O no bloquea el event loop.
@router.post("/postulaciones", status_code=201)
def crear_postulacion(
    background: BackgroundTasks,
    vacante_id: str = Form(),
    nombre: str = Form(min_length=1, max_length=200),
    email: str = Form(max_length=254, pattern=EMAIL_RE),
    consentimiento: bool = Form(),
    pdf: UploadFile = File(),
    session: Session = Depends(get_session),
    evaluador: Evaluador = Depends(get_evaluador),
    uploads: Path = Depends(get_uploads_dir),
):
    vacante = next((v for v in _vacantes() if v.id == vacante_id), None)
    if vacante is None:
        _rechazar(session, 404, "Vacante no encontrada", vacante_id)
    if not consentimiento:
        _rechazar(session, 422, "Se requiere el consentimiento (Ley 1581)", vacante_id)
    if pdf.content_type != "application/pdf":
        _rechazar(session, 415, "Solo se aceptan archivos PDF", vacante_id)
    contenido = pdf.file.read(MAX_PDF_BYTES + 1)
    if len(contenido) > MAX_PDF_BYTES:
        _rechazar(session, 413, "El PDF supera 5 MB", vacante_id)
    if not contenido.startswith(b"%PDF"):
        _rechazar(session, 415, "El archivo no es un PDF válido", vacante_id)
    try:
        extraer_texto_pdf(contenido)  # el candidato ve este error al momento
    except (PdfInvalidoError, PdfSinTextoError) as exc:
        _rechazar(session, *ERRORES_PDF[type(exc)], vacante_id)

    ev = _persistir(session, uploads, contenido, vacante_id, nombre, email)
    background.add_task(evaluar_en_segundo_plano, ev.id, evaluador, uploads)
    return {"evaluacion_id": ev.id, "estado": ev.estado}


def _fila(ev: Evaluacion, post: Postulacion, cand: Candidato) -> dict:
    return {"id": ev.id, "vacante_id": post.vacante_id, "candidato": cand.nombre,
            "puntaje_total": ev.puntaje_total, "veredicto_sugerido": ev.veredicto_ia,
            "veredicto_final": ev.veredicto_final, "estado": ev.estado}


@router.get("/evaluaciones")
def listar_evaluaciones(vacante_id: str | None = None, estado: str | None = None,
                        limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
                        session: Session = Depends(get_session)):
    q = (select(Evaluacion, Postulacion, Candidato)
         .join(Postulacion, Evaluacion.postulacion_id == Postulacion.id)
         .join(Candidato, Postulacion.candidato_id == Candidato.id)
         .order_by(case((Evaluacion.estado == "en_evaluacion", 1),
                        (Evaluacion.estado == "error_evaluacion", 2), else_=0),
                   Evaluacion.puntaje_total.desc(), Evaluacion.id))
    if vacante_id:
        q = q.where(Postulacion.vacante_id == vacante_id)
    if estado:
        q = q.where(Evaluacion.estado == estado)
    return [_fila(*r) for r in session.exec(q.limit(limit).offset(offset)).all()]


@router.get("/evaluaciones/{evaluacion_id}")
def obtener_evaluacion(evaluacion_id: int, session: Session = Depends(get_session)):
    ev = session.get(Evaluacion, evaluacion_id)
    if ev is None:
        raise HTTPException(404, "Evaluación no encontrada")
    post = session.get(Postulacion, ev.postulacion_id)
    cand = session.get(Candidato, post.candidato_id)
    return {"id": ev.id, "vacante_id": post.vacante_id, "candidato": cand.nombre,
            "perfil": ev.perfil, "resultado": ev.resultado,
            "veredicto_final": ev.veredicto_final, "estado": ev.estado, "error": ev.error,
            "entrevista": ({"inicio": ev.entrevista_inicio, "meet_link": ev.entrevista_link}
                           if ev.entrevista_link else None)}


@router.post("/evaluaciones/{evaluacion_id}/reintentar", status_code=202)
def reintentar(evaluacion_id: int, background: BackgroundTasks,
               session: Session = Depends(get_session),
               evaluador: Evaluador = Depends(get_evaluador),
               uploads: Path = Depends(get_uploads_dir)):
    ev = session.get(Evaluacion, evaluacion_id)
    if ev is None:
        raise HTTPException(404, "Evaluación no encontrada")
    # UPDATE condicional: un doble clic no programa dos evaluaciones. Se admite también
    # en_evaluacion si lleva más de MINUTOS_EVALUACION_ATASCADA (la tarea se perdió).
    ahora = datetime.now(timezone.utc)
    atascada = and_(Evaluacion.estado == "en_evaluacion", Evaluacion.evaluacion_iniciada_at
                    < ahora - timedelta(minutes=MINUTOS_EVALUACION_ATASCADA))
    res = session.connection().execute(
        update(Evaluacion).where(Evaluacion.id == evaluacion_id,
                                 or_(Evaluacion.estado == "error_evaluacion", atascada))
        .values(estado="en_evaluacion", error=None, evaluacion_iniciada_at=ahora))
    session.commit()
    if res.rowcount == 0:
        raise HTTPException(409, "Solo se reintentan evaluaciones en error o atascadas")
    background.add_task(evaluar_en_segundo_plano, evaluacion_id, evaluador, uploads)
    return {"id": evaluacion_id, "estado": "en_evaluacion"}


class DecisionIn(BaseModel):
    veredicto: Veredicto
    motivo: str | None = Field(default=None, min_length=1, max_length=1000)
    reclutador: str = Field(min_length=1, max_length=100)


@router.post("/evaluaciones/{evaluacion_id}/decision")
def decidir(evaluacion_id: int, body: DecisionIn, session: Session = Depends(get_session),
            notificador=Depends(get_notificador)):
    ev = session.get(Evaluacion, evaluacion_id)
    if ev is None:
        raise HTTPException(404, "Evaluación no encontrada")
    if ev.estado != "pendiente_revision":
        raise HTTPException(409, "La evaluación ya fue decidida" if ev.estado == "decidida"
                            else "La evaluación aún no está lista para decidir")
    if body.veredicto.value != ev.veredicto_ia and not (body.motivo or "").strip():
        raise HTTPException(422, "Se requiere motivo si el veredicto difiere del sugerido")
    # UPDATE condicional: solo una decisión concurrente gana.
    res = session.connection().execute(
        update(Evaluacion)
        .where(Evaluacion.id == evaluacion_id, Evaluacion.estado == "pendiente_revision")
        .values(veredicto_final=body.veredicto.value, estado="decidida",
                decidido_por=body.reclutador, motivo=body.motivo))
    if res.rowcount == 0:
        session.rollback()
        raise HTTPException(409, "La evaluación ya fue decidida")
    _auditar(session, "decision", evaluacion_id,
             {"veredicto_ia": ev.veredicto_ia, "veredicto_final": body.veredicto.value,
              "motivo": body.motivo, "reclutador": body.reclutador})
    session.commit()
    entrevista = _notificar(session, notificador, ev, body.veredicto, body.motivo)
    return {"id": evaluacion_id, "veredicto_final": body.veredicto.value, "estado": "decidida",
            "entrevista": entrevista}


SIN_DETALLE = "Tu perfil no se ajustó a los requisitos de esta vacante en este momento."
CIFRAS_RE = re.compile(r"\d+(?:[.,]\d+)?\s*%?")


def _explicaciones(resultado: dict, contradice_ia: bool, motivo: str | None) -> list[str]:
    """Una línea por criterio faltante, sin cifras; si el reclutador contradijo a la IA, su motivo."""
    if contradice_ia and (motivo or "").strip():
        return [motivo.strip()]
    lineas = []
    for c in resultado.get("criterios", []):
        nota = CIFRAS_RE.sub("", c.get("nota") or "").strip()
        if c.get("faltantes") and nota:
            lineas.append(f"{c['criterio'].replace('_', ' ').capitalize()}: {nota}")
    return lineas or [SIN_DETALLE]


def _notificar(session: Session, notificador, ev: Evaluacion, veredicto: Veredicto,
               motivo: str | None = None) -> dict | None:
    """Correo/agenda tras confirmar la decisión. Un fallo de Google solo se audita."""
    if veredicto == Veredicto.REVISION_HUMANA:
        return None
    if not notificador.habilitado:
        _auditar(session, "notificacion_omitida", ev.id, {"veredicto": veredicto.value})
        session.commit()
        return None
    post = session.get(Postulacion, ev.postulacion_id)
    cand = session.get(Candidato, post.candidato_id)
    vacante = next((v.titulo for v in _vacantes() if v.id == post.vacante_id), post.vacante_id)
    entrevista = None
    paso = "evento"
    try:
        if veredicto == Veredicto.ENTREVISTA:
            inicio = siguiente_horario(datetime.now(timezone.utc))
            entrevista = notificador.crear_entrevista(
                cand.email, f"Entrevista: {vacante}", f"Entrevista con {cand.nombre}", inicio)
            paso = "meet"
            if not entrevista.get("meet_link"):
                raise ValueError("El evento no trae enlace de Meet")
            # Se guarda ya: el evento existe aunque luego falle el correo.
            session.connection().execute(update(Evaluacion).where(Evaluacion.id == ev.id).values(
                entrevista_inicio=entrevista["inicio"], entrevista_link=entrevista["meet_link"]))
            session.commit()
            asunto, cuerpo = correo_invitacion(
                cand.nombre, vacante, entrevista["inicio"], entrevista["meet_link"])
        else:
            paso = "plantilla"
            asunto, cuerpo = correo_no_continua(cand.nombre, vacante, _explicaciones(
                ev.resultado, veredicto.value != ev.veredicto_ia, motivo))
        paso = "correo"
        notificador.enviar_correo(cand.email, asunto, cuerpo)
        _auditar(session, "notificacion_enviada", ev.id, {"veredicto": veredicto.value})
    except Exception as exc:
        session.rollback()
        _auditar(session, "notificacion_fallida", ev.id, {
            "veredicto": veredicto.value, "error": type(exc).__name__, "paso": paso,
            "event_id": (entrevista or {}).get("event_id")})
    session.commit()
    return ({"inicio": entrevista["inicio"], "meet_link": entrevista.get("meet_link")}
            if entrevista else None)


def _vacantes():
    from app.main import _cargar_vacantes  # import tardío: main importa este módulo
    return _cargar_vacantes()
