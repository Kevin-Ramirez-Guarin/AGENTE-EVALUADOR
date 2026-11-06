"""Rutas de postulaciones y evaluaciones (docs/api.md)."""
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import NoReturn

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlmodel import Session, select

from app.db import Auditoria, Candidato, Evaluacion, Postulacion, get_session
from app.evaluador import Evaluador, get_evaluador
from app.models import Veredicto

router = APIRouter()

MAX_PDF_BYTES = 5 * 1024 * 1024
UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"


def get_uploads_dir() -> Path:
    return UPLOADS_DIR


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
               nombre: str, email: str, perfil, resultado) -> Evaluacion:
    """Escribe el PDF y las filas; si algo falla, borra el PDF y hace rollback."""
    uploads.mkdir(parents=True, exist_ok=True)
    # El nombre en disco es un UUID; el nombre del cliente nunca se usa.
    destino = uploads / f"{uuid.uuid4()}.pdf"
    try:
        destino.write_bytes(contenido)
        candidato = Candidato(nombre=nombre, email=email)
        session.add(candidato)
        session.flush()
        consentimiento_at = datetime.now(timezone.utc)
        post = Postulacion(candidato_id=candidato.id, vacante_id=vacante_id,
                           pdf_path=destino.name, consentimiento_at=consentimiento_at)
        session.add(post)
        session.flush()
        ev = Evaluacion(postulacion_id=post.id, puntaje_total=resultado.puntaje_total,
                        perfil=perfil.model_dump(mode="json"),
                        resultado=resultado.model_dump(mode="json"),
                        veredicto_ia=resultado.veredicto_sugerido.value)
        session.add(ev)
        session.flush()
        _auditar(session, "evaluacion_creada", ev.id,
                 {"vacante_id": vacante_id, "veredicto_sugerido": ev.veredicto_ia,
                  "puntaje_total": ev.puntaje_total,
                  "consentimiento_at": consentimiento_at.isoformat()})
        session.commit()
        return ev
    except Exception:
        session.rollback()
        destino.unlink(missing_ok=True)
        raise


# Función síncrona: FastAPI la corre en un hilo, así el I/O y el evaluador no bloquean el event loop.
@router.post("/postulaciones", status_code=201)
def crear_postulacion(
    vacante_id: str = Form(),
    nombre: str = Form(),
    email: str = Form(),
    consentimiento: bool = Form(),
    pdf: UploadFile = File(),
    session: Session = Depends(get_session),
    evaluador: Evaluador = Depends(get_evaluador),
    uploads: Path = Depends(get_uploads_dir),
):
    from app.main import _cargar_vacantes  # import tardío: main importa este módulo

    vacante = next((v for v in _cargar_vacantes() if v.id == vacante_id), None)
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
        perfil, resultado = evaluador(contenido, vacante)
    except Exception as exc:
        _auditar(session, "evaluacion_fallida", None,
                 {"vacante_id": vacante_id, "error": type(exc).__name__})
        session.commit()
        raise HTTPException(502, "No se pudo evaluar la hoja de vida") from exc

    ev = _persistir(session, uploads, contenido, vacante_id, nombre, email, perfil, resultado)
    return {"evaluacion_id": ev.id, "estado": ev.estado}


def _fila(ev: Evaluacion, post: Postulacion, cand: Candidato) -> dict:
    return {"id": ev.id, "vacante_id": post.vacante_id, "candidato": cand.nombre,
            "puntaje_total": ev.puntaje_total, "veredicto_sugerido": ev.veredicto_ia,
            "veredicto_final": ev.veredicto_final, "estado": ev.estado}


@router.get("/evaluaciones")
def listar_evaluaciones(vacante_id: str | None = None, estado: str | None = None,
                        session: Session = Depends(get_session)):
    q = (select(Evaluacion, Postulacion, Candidato)
         .join(Postulacion, Evaluacion.postulacion_id == Postulacion.id)
         .join(Candidato, Postulacion.candidato_id == Candidato.id)
         .order_by(Evaluacion.puntaje_total.desc(), Evaluacion.id))
    if vacante_id:
        q = q.where(Postulacion.vacante_id == vacante_id)
    if estado:
        q = q.where(Evaluacion.estado == estado)
    return [_fila(*r) for r in session.exec(q).all()]


@router.get("/evaluaciones/{evaluacion_id}")
def obtener_evaluacion(evaluacion_id: int, session: Session = Depends(get_session)):
    ev = session.get(Evaluacion, evaluacion_id)
    if ev is None:
        raise HTTPException(404, "Evaluación no encontrada")
    post = session.get(Postulacion, ev.postulacion_id)
    cand = session.get(Candidato, post.candidato_id)
    return {"id": ev.id, "vacante_id": post.vacante_id, "candidato": cand.nombre,
            "perfil": ev.perfil, "resultado": ev.resultado,
            "veredicto_final": ev.veredicto_final, "estado": ev.estado}


class DecisionIn(BaseModel):
    veredicto: Veredicto
    motivo: str | None = None
    reclutador: str


@router.post("/evaluaciones/{evaluacion_id}/decision")
def decidir(evaluacion_id: int, body: DecisionIn, session: Session = Depends(get_session)):
    ev = session.get(Evaluacion, evaluacion_id)
    if ev is None:
        raise HTTPException(404, "Evaluación no encontrada")
    if ev.estado == "decidida":
        raise HTTPException(409, "La evaluación ya fue decidida")
    if body.veredicto.value != ev.veredicto_ia and not (body.motivo or "").strip():
        raise HTTPException(422, "Se requiere motivo si el veredicto difiere del sugerido")
    ev.veredicto_final = body.veredicto.value
    ev.estado = "decidida"
    ev.decidido_por = body.reclutador
    ev.motivo = body.motivo
    session.add(ev)
    _auditar(session, "decision", ev.id,
             {"veredicto_ia": ev.veredicto_ia, "veredicto_final": ev.veredicto_final,
              "motivo": body.motivo, "reclutador": body.reclutador})
    session.commit()
    # Sprint actual: no se envían correos ni se agenda; `entrevista` queda en null.
    return {"id": ev.id, "veredicto_final": ev.veredicto_final, "estado": ev.estado, "entrevista": None}
