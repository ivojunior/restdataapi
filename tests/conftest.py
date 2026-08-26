import os

os.environ.setdefault("API_KEY", "test-key")
os.environ.setdefault("SESSION_SECRET", "test-session-secret-com-32-bytes-ou-mais")
os.environ.setdefault("ALLOWED_GOOGLE_DOMAINS", "empresa-teste.com.br")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-google-client-id")
# Secure exige HTTPS; o TestClient conversa em http com um host fake
# ("testserver") — sem isto o cookie de sessão não seria reenviado nas
# requisições seguintes dentro do mesmo teste.
os.environ.setdefault("SESSION_COOKIE_SECURE", "false")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

TEST_API_KEY = os.environ["API_KEY"]

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def _setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"X-API-Key": TEST_API_KEY}


@pytest.fixture
def db_session():
    """Sessão para inserir dados de teste diretamente, já que a API é somente leitura."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def mock_google_id_token(monkeypatch):
    """Substitui a verificação real do token do Google (que bateria na rede)
    por uma função controlável pelo teste. Uso:

        mock_google_id_token(email="fulano@empresa-teste.com.br")
        # ou, para simular token inválido:
        mock_google_id_token(erro=True)
    """
    from app.auth_google import GoogleUserInfo

    def _configurar(email: str = "usuario@empresa-teste.com.br", nome: str = "Usuário Teste",
                     erro: bool = False):
        def _fake_verify(credential: str) -> GoogleUserInfo:
            if erro:
                raise ValueError("token de teste inválido")
            return GoogleUserInfo(email=email, nome=nome, hd=email.rsplit("@", 1)[-1])

        monkeypatch.setattr("app.routers.auth.verify_google_id_token", _fake_verify)

    return _configurar
