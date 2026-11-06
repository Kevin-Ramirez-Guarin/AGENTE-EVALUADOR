from sqlalchemy import text

from app.db import make_engine


def test_sqlite_usa_wal_y_busy_timeout(tmp_path):
    eng = make_engine(f"sqlite:///{tmp_path / 'wal.db'}")
    with eng.connect() as c:
        assert c.execute(text("PRAGMA journal_mode")).scalar() == "wal"
        assert c.execute(text("PRAGMA busy_timeout")).scalar() >= 5000


def test_bd_existente_recibe_las_columnas_nuevas(tmp_path):
    from app.db import crear_esquema

    engine = make_engine(f"sqlite:///{tmp_path / 'vieja.db'}")
    with engine.begin() as c:  # tabla de una versión anterior, sin las columnas de la entrevista
        c.execute(text("CREATE TABLE evaluacion (id INTEGER PRIMARY KEY, postulacion_id INTEGER, estado VARCHAR)"))
    crear_esquema(engine)
    crear_esquema(engine)  # idempotente
    with engine.connect() as c:
        cols = {r[1] for r in c.execute(text("PRAGMA table_info(evaluacion)"))}
    assert {"entrevista_inicio", "entrevista_link"} <= cols
