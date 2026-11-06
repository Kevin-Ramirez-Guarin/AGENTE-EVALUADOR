"""Persistencia SQLModel/SQLite (PLAN.md §6)."""
import os
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, event
from sqlmodel import Field, Session, SQLModel, create_engine

DEFAULT_DATABASE_URL = "sqlite:///./agente.db"


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Candidato(SQLModel, table=True):
    """Contacto, separado de la HV y de la evaluación."""
    id: int | None = Field(default=None, primary_key=True)
    nombre: str
    email: str


class Postulacion(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    candidato_id: int = Field(foreign_key="candidato.id")
    vacante_id: str = Field(index=True)
    pdf_path: str
    consentimiento_at: datetime
    creada_at: datetime = Field(default_factory=_now)


class Evaluacion(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    postulacion_id: int = Field(foreign_key="postulacion.id")
    # Nulos mientras la evaluación está en segundo plano (o si falló).
    puntaje_total: float | None = Field(default=None, index=True)
    perfil: dict | None = Field(default=None, sa_column=Column(JSON(none_as_null=True)))
    resultado: dict | None = Field(default=None, sa_column=Column(JSON(none_as_null=True)))
    veredicto_ia: str | None = None
    veredicto_final: str | None = None
    # en_evaluacion -> pendiente_revision | error_evaluacion; pendiente_revision -> decidida.
    # Sin migración: la BD SQLite se crea nueva en cada demo.
    estado: str = "en_evaluacion"
    error: str | None = None
    decidido_por: str | None = None
    motivo: str | None = None


class Auditoria(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    evaluacion_id: int | None = Field(default=None, foreign_key="evaluacion.id")
    evento: str
    timestamp: datetime = Field(default_factory=_now)
    detalle: str = ""


def make_engine(url: str | None = None):
    url = url or os.getenv("DATABASE_URL") or DEFAULT_DATABASE_URL
    args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=args)
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _pragmas(dbapi_conn, _):
            # WAL: lectores y un escritor a la vez; busy_timeout: espera en vez de "database is locked".
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA busy_timeout=10000")
            cur.close()
    return engine


_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = make_engine()
        SQLModel.metadata.create_all(_engine)
    return _engine


def get_session():
    with Session(get_engine()) as session:
        yield session
