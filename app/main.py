import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings

logger = logging.getLogger("restdataapi")

from app.routers import (
    cargas, faturamento, financeiro, fornecedores, produtos, saldos_estoque,
    titulos_pagar,
)

app = FastAPI(
    title="RestDataAPI",
    description="API REST para acesso a dados do Protheus.",
    version="1.0.0",
    # Em ambientes expostos externamente, defina DOCS_ENABLED=false no .env
    # para não publicar o schema completo da API sem exigir autenticação.
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
)

# Limite de requisições por IP, aplicado a todas as rotas via SlowAPIMiddleware
# (mitiga brute-force de API key e abuso/DoS acidental). Configurável via
# RATE_LIMIT_DEFAULT no .env (padrão "100/minute").
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit_default])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(titulos_pagar.router)
app.include_router(fornecedores.router)
app.include_router(saldos_estoque.router)
app.include_router(produtos.router)
app.include_router(financeiro.router)
app.include_router(cargas.router)
app.include_router(faturamento.router)


@app.exception_handler(SQLAlchemyError)
def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    # Sem isto, o traceback real do erro de banco era descartado silenciosamente
    # (o handler substitui o comportamento padrão do Starlette de logar exceções
    # não tratadas) — dificultando diagnosticar erros 500 reportados por clientes.
    #
    # Passa `exc` explicitamente em exc_info: handlers de exceção síncronos são
    # executados pelo Starlette num thread de threadpool, onde sys.exc_info()
    # (usado por logger.exception()) já não enxerga a exceção — sem isso o log
    # sai como "NoneType: None" em vez do traceback real.
    logger.error(
        "Erro de banco de dados em %s %s", request.method, request.url, exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "Erro ao acessar o banco de dados"})


@app.get("/", tags=["Health"])
def raiz():
    return {"nome": "RestDataAPI", "status": "online"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
