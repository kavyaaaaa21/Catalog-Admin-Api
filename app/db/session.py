import warnings

from sqlalchemy import create_engine, event
from sqlalchemy.exc import SAWarning
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Numeric columns on SQLite round-trip through float; harmless for this project.
warnings.filterwarnings("ignore", message=".*does \\*not\\* support Decimal.*", category=SAWarning)


def make_engine(url: str, **kwargs):
    if url.startswith("sqlite"):
        kwargs.setdefault("connect_args", {"check_same_thread": False})
    engine = create_engine(url, **kwargs)

    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _enable_fk(dbapi_conn, _):  # SQLite ignores FKs unless asked
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()

    return engine


engine = make_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
