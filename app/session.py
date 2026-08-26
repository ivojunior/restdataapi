from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt

from app.config import settings

_ALGORITHM = "HS256"


@dataclass
class SessionUser:
    email: str
    nome: str


def criar_sessao_jwt(email: str, nome: str) -> str:
    """Emite o JWT de sessão da própria aplicação (não o ID token do Google,
    que expira em ~1h e não foi desenhado como sessão de app — ver
    app/auth_google.py)."""
    agora = datetime.now(timezone.utc)
    payload = {
        "sub": email,
        "nome": nome,
        "iat": agora,
        "exp": agora + timedelta(minutes=settings.session_ttl_minutes),
    }
    return jwt.encode(payload, settings.session_secret, algorithm=_ALGORITHM)


def verificar_sessao_jwt(token: str) -> SessionUser:
    """Decodifica e valida o JWT de sessão (assinatura + expiração).

    JWT stateless: uma sessão emitida não pode ser revogada antes de expirar
    (trade-off aceito — TTL curto de 8h compensa; ver plano de implementação).
    """
    try:
        payload = jwt.decode(token, settings.session_secret, algorithms=[_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise ValueError(f"Sessão inválida ou expirada: {exc}") from exc

    return SessionUser(email=payload["sub"], nome=payload.get("nome", payload["sub"]))
