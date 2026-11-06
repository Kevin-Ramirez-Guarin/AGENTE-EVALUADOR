"""Persistencia SQLModel/SQLite (PLAN.md §6)."""
import os
from datetime import datetime, timedelta, timezone

from sqlalchemy import JSON, Column, event
from sqlmodel import Field, Session, SQLModel, create_engine, select

DEFAULT_DATABASE_URL = "sqlite:///./agente.db"
MINUTOS_EVALUACION_ATASCADA = 10  # en_evaluacion por más de esto se considera perdida


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
    evaluacion_iniciada_at: datetime | None = Field(default_factory=_now)
    decidido_por: str | None = None
    motivo: str | None = None
    # Entrevista agendada al aprobar: inicio ISO con zona horaria y enlace de Meet.
    entrevista_inicio: str | None = None
    entrevista_link: str | None = None


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


def crear_esquema(engine) -> None:
    """Crea las tablas y, en una BD SQLite de una versión anterior, agrega las columnas nulas que falten."""
    SQLModel.metadata.create_all(engine)
    if engine.dialect.name != "sqlite":
        return
    with engine.begin() as c:
        for tabla in SQLModel.metadata.sorted_tables:  # nombres internos, no datos del usuario
            existentes = {r[1] for r in c.exec_driver_sql(f"PRAGMA table_info({tabla.name})")}
            for col in tabla.columns:
                if col.name not in existentes and col.nullable:
                    tipo = col.type.compile(engine.dialect)
                    c.exec_driver_sql(f"ALTER TABLE {tabla.name} ADD COLUMN {col.name} {tipo}")


_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = make_engine()
        crear_esquema(_engine)
    return _engine


def marcar_interrumpidas(session: Session, ahora: datetime | None = None) -> int:
    """Al arrancar: las en_evaluacion atascadas (el proceso murió) pasan a error_evaluacion."""
    corte = (ahora or _now()) - timedelta(minutes=MINUTOS_EVALUACION_ATASCADA)
    filas = session.exec(select(Evaluacion).where(
        Evaluacion.estado == "en_evaluacion", Evaluacion.evaluacion_iniciada_at < corte)).all()
    for ev in filas:
        ev.estado, ev.error = "error_evaluacion", "interrumpida"
        session.add(ev)
    session.commit()
    return len(filas)


def get_session():
    with Session(get_engine()) as session:
        yield session
