"""Retención de datos personales (Ley 1581, PLAN.md §7).

Borra el PDF y anonimiza nombre y correo de las postulaciones con más de N días. Conserva
evaluaciones y decisiones (evidencia del humano en el bucle) y deja auditoría `datos_purgados`.

Uso (desde backend/): python -m scripts.purgar_datos [--dias 180] [--dry-run]
"""
import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlmodel import Session, select

from app.db import Auditoria, Candidato, Evaluacion, Postulacion, get_engine
from app.routes import get_uploads_dir

ELIMINADO = "[eliminado]"


def purgar(session: Session, uploads: Path, dias: int, dry_run: bool = False,
           ahora: datetime | None = None) -> int:
    """Devuelve cuántas postulaciones se purgaron (o se purgarían con dry_run)."""
    corte = ((ahora or datetime.now(timezone.utc)) - timedelta(days=dias))
    viejas = session.exec(select(Postulacion).where(
        Postulacion.creada_at < corte, Postulacion.pdf_path != ELIMINADO)).all()
    if dry_run:
        return len(viejas)
    for post in viejas:
        (uploads / post.pdf_path).unlink(missing_ok=True)
        cand = session.get(Candidato, post.candidato_id)
        cand.nombre = cand.email = ELIMINADO
        post.pdf_path = ELIMINADO
        ev = session.exec(select(Evaluacion).where(Evaluacion.postulacion_id == post.id)).first()
        session.add(Auditoria(evento="datos_purgados", evaluacion_id=ev.id if ev else None,
                              detalle=json.dumps({"postulacion_id": post.id, "dias": dias})))
    session.commit()
    return len(viejas)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dias", type=int, default=180)
    ap.add_argument("--dry-run", action="store_true", help="solo cuenta, no borra")
    args = ap.parse_args(argv)
    with Session(get_engine()) as session:
        n = purgar(session, get_uploads_dir(), args.dias, args.dry_run)
    print(f"{'Se purgarían' if args.dry_run else 'Purgadas'} {n} postulaciones de más de {args.dias} días")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
