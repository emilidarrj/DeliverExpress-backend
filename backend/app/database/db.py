"""Conexion SQLAlchemy con el esquema deliverexpress. roadmap §1."""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

# search_path por conexion: asi de_app ve el esquema sin prefijar en cada query.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args={"options": "-c search_path=deliverexpress"},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """Dependencia FastAPI: abre sesion, la cede y la cierra."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()