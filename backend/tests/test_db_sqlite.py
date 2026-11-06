from sqlalchemy import text

from app.db import make_engine


def test_sqlite_usa_wal_y_busy_timeout(tmp_path):
    eng = make_engine(f"sqlite:///{tmp_path / 'wal.db'}")
    with eng.connect() as c:
        assert c.execute(text("PRAGMA journal_mode")).scalar() == "wal"
        assert c.execute(text("PRAGMA busy_timeout")).scalar() >= 5000
