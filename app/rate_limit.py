from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

# Instância única, compartilhada entre app/main.py (middleware + limite padrão
# global) e routers que precisam de um limite mais restrito em endpoints
# específicos (ex. app/routers/auth.py em /auth/google). Extraído para módulo
# próprio para evitar import circular: app/main.py importa app/routers/*, que
# por sua vez precisariam importar de volta app/main.py para usar o limiter.
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit_default])
