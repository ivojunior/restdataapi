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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

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
