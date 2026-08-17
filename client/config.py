"""Configurações do cliente lidas de variáveis de ambiente ou arquivo .env."""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY      = os.getenv("API_KEY",      "troque-esta-chave-por-uma-secreta")
API_KEY_NAME = os.getenv("API_KEY_NAME", "X-API-Key")
