from dataclasses import dataclass

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.config import settings

_google_request = google_requests.Request()


@dataclass
class GoogleUserInfo:
    email: str
    nome: str
    hd: str | None  # hosted domain do Google Workspace, se presente


def verify_google_id_token(credential: str) -> GoogleUserInfo:
    """Valida um ID token do Google Identity Services (assinatura, `aud`, `exp`)
    e devolve os dados do usuário autenticado.

    Nunca confiar no client-side: o credential chega do frontend, mas quem
    verifica a assinatura contra as chaves públicas do Google (e o `aud` contra
    google_client_id) é sempre o backend, via google-auth.
    """
    try:
        payload = id_token.verify_oauth2_token(
            credential, _google_request, audience=settings.google_client_id,
        )
    except ValueError as exc:
        raise ValueError(f"ID token do Google inválido: {exc}") from exc

    return GoogleUserInfo(
        email=payload["email"],
        nome=payload.get("name", payload["email"]),
        hd=payload.get("hd"),
    )


def domain_permitido(email: str) -> bool:
    """Confere o domínio do e-mail contra a allowlist de configuração.

    Não usa o claim `hd` do token para essa decisão — `hd` é só metadado
    (ausente em contas pessoais, e mesmo presente é redundante com o e-mail
    verificado); a fonte de verdade é sempre o domínio do e-mail já validado
    por verify_google_id_token. Lista vazia em settings = nega tudo (falha
    fechado, nunca "permite qualquer domínio" por omissão de configuração).
    """
    dominio = email.rsplit("@", 1)[-1].lower()
    return dominio in settings.allowed_google_domains_set
