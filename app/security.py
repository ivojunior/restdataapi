import secrets

from fastapi import Security, status
from fastapi.exceptions import HTTPException
from fastapi.security.api_key import APIKeyHeader

from app.config import settings

_api_key_header = APIKeyHeader(name=settings.api_key_name, auto_error=False)


def verify_api_key(api_key: str = Security(_api_key_header)) -> str:
    """Valida a API Key contra o mapa de chaves nomeadas (settings.api_keys_map).

    Usa secrets.compare_digest (tempo constante) em vez de `==`: uma
    comparação de string comum vaza, pelo tempo de resposta, quantos
    caracteres do início da chave estão corretos.
    """
    if api_key:
        for nome_cliente, chave_valida in settings.api_keys_map.items():
            if secrets.compare_digest(api_key, chave_valida):
                return nome_cliente
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="API key inválida ou ausente",
    )
