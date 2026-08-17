from functools import lru_cache

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import settings

Base = declarative_base()


def _bloquear_escrita(session: Session, flush_context, instances) -> None:
    """Impede qualquer INSERT/UPDATE/DELETE: esta API é somente leitura (SELECT)."""
    if session.new or session.dirty or session.deleted:
        raise PermissionError(
            "Operações de escrita (INSERT/UPDATE/DELETE) não são permitidas. "
            "Esta API é somente leitura."
        )


@lru_cache
def get_engine():
    return create_engine(settings.database_url, pool_pre_ping=True)


@lru_cache
def get_session_local():
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    event.listens_for(session_local, "before_flush")(_bloquear_escrita)
    return session_local


def get_db():
    db = get_session_local()()
    try:
        yield db
    finally:
        db.close()
