import secrets
from typing import Optional

from fastapi import Request, Security, status
from fastapi.exceptions import HTTPException
from fastapi.security.api_key import APIKeyHeader

from app.config import settings
from app.session import verificar_sessao_jwt

_api_key_header = APIKeyHeader(name=settings.api_key_name, auto_error=False)


def _validar_api_key(api_key: Optional[str]) -> Optional[str]:
    """Retorna o nome do cliente se `api_key` bater com alguma chave válida,
    None caso contrário (nunca levanta — quem decide o que fazer com None é
    o chamador)."""
    if not api_key:
        return None
    for nome_cliente, chave_valida in settings.api_keys_map.items():
        # secrets.compare_digest (tempo constante) em vez de `==`: uma
        # comparação de string comum vaza, pelo tempo de resposta, quantos
        # caracteres do início da chave estão corretos.
        if secrets.compare_digest(api_key, chave_valida):
            return nome_cliente
    return None


def verify_api_key(api_key: str = Security(_api_key_header)) -> str:
    """Valida a API Key contra o mapa de chaves nomeadas (settings.api_keys_map).

    Mecanismo original, usado pelos clients desktop (Tkinter). Ver
    verify_api_key_or_session para o gate combinado usado pelos routers de
    dados, que também aceita a sessão de login Google da SPA.
    """
    nome_cliente = _validar_api_key(api_key)
    if nome_cliente is not None:
        return nome_cliente
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="API key inválida ou ausente",
    )


def verify_api_key_or_session(
    request: Request, api_key: Optional[str] = Security(_api_key_header),
) -> str:
    """Gate de acesso dos routers de dados: aceita API Key (clients Tkinter,
    inalterado) OU cookie de sessão de login Google (SPA) — nunca exige os
    dois, nunca remove o suporte a nenhum dos dois.

    API key é checada primeiro (comparação local, mais barata que decodificar
    um JWT); o cookie de sessão só é olhado se não vier API key ou se ela for
    inválida. Retorna uma string identificando quem fez a requisição (nome do
    cliente da API key, ou o e-mail do usuário logado via Google) — hoje usada
    só como gate de acesso, não para lógica de negócio.
    """
    nome_cliente = _validar_api_key(api_key)
    if nome_cliente is not None:
        return nome_cliente

    cookie = request.cookies.get(settings.session_cookie_name)
    if cookie:
        try:
            return verificar_sessao_jwt(cookie).email
        except ValueError:
            pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não autenticado (API key ou sessão inválida/ausente)",
    )
