import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, _bloquear_escrita
from app.models.fornecedor import Fornecedor


def test_flush_com_escrita_pendente_e_bloqueado():
    """Garante que a proteção contra INSERT/UPDATE/DELETE funciona mesmo em nível de ORM,
    independentemente de quais rotas existem na API."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_local = sessionmaker(bind=engine)
    event.listens_for(session_local, "before_flush")(_bloquear_escrita)

    session = session_local()
    session.add(Fornecedor(filial="01", codigo="000001", loja="01", nome="Teste"))

    with pytest.raises(PermissionError):
        session.commit()

    session.close()
