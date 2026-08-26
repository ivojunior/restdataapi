from typing import Dict
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_server: str = "localhost"
    db_port: int = 1433
    db_name: str = "master"
    db_user: str = "sa"
    db_password: str = ""
    db_driver: str = "ODBC Driver 17 for SQL Server"

    api_key: str = "change-me"
    api_key_name: str = "X-API-Key"
    # Chaves nomeadas adicionais, formato "cliente1:chave1,cliente2:chave2".
    # Permite revogar/identificar o acesso de um cliente sem afetar os demais.
    # Quando vazio, cai no api_key único acima (retrocompatibilidade).
    api_keys: str = ""

    rate_limit_default: str = "100/minute"

    docs_enabled: bool = True

    # Login via Google Workspace (SPA) — coexiste com API Key, nunca a
    # substitui (ver app/security.py:verify_api_key_or_session).
    google_client_id: str = ""
    # Domínios do Google Workspace autorizados a logar, formato
    # "empresa.com.br,outraempresa.com". Vazio = nega todo mundo (falha
    # fechado — nunca "permite tudo" por omissão de configuração).
    allowed_google_domains: str = ""
    # Segredo para assinar o JWT de sessão próprio da aplicação (não é o
    # token do Google, que expira em ~1h e não foi desenhado como sessão de
    # app). Gerar com `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
    session_secret: str = "change-me"
    session_cookie_name: str = "rda_session"
    session_ttl_minutes: int = 480  # 8h — uma jornada de trabalho
    # Cookie Secure exige HTTPS; True em produção. Só desligar em dev local
    # servindo via http://localhost.
    session_cookie_secure: bool = True
    # Origem da SPA, para restringir o CORS (allow_origins=["*"] é
    # incompatível com allow_credentials=True, exigido pelo cookie de
    # sessão). Vazio = nenhuma origem cross-site liberada (uso normal
    # quando a SPA é servida pelo próprio FastAPI, mesma origem).
    frontend_origin: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def allowed_google_domains_set(self) -> set:
        """Conjunto de domínios permitidos (lowercase), a partir de allowed_google_domains."""
        return {
            item.strip().lower()
            for item in self.allowed_google_domains.split(",")
            if item.strip()
        }

    @property
    def api_keys_map(self) -> Dict[str, str]:
        """Mapa nome-do-cliente -> chave válida."""
        pares: Dict[str, str] = {}
        for item in self.api_keys.split(","):
            item = item.strip()
            if not item:
                continue
            nome, _, chave = item.partition(":")
            nome, chave = nome.strip(), chave.strip()
            if nome and chave:
                pares[nome] = chave
        if not pares:
            pares["default"] = self.api_key
        return pares

    @property
    def database_url(self) -> str:
        odbc_params = (
            f"DRIVER={{{self.db_driver}}};"
            f"SERVER={self.db_server},{self.db_port};"
            f"DATABASE={self.db_name};"
            f"UID={self.db_user};"
            f"PWD={self.db_password};"
            "TrustServerCertificate=yes;"
        )
        return f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc_params)}"


settings = Settings()
