import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.rate_limit import limiter

logger = logging.getLogger("restdataapi")

from app.routers import (
    auth, cargas, faturamento, financeiro, fornecedores, produtos,
    saldos_estoque, titulos_pagar,
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
# RATE_LIMIT_DEFAULT no .env (padrão "100/minute"). O `limiter` em si vive em
# app/rate_limit.py (não aqui) para que routers como app/routers/auth.py
# possam importá-lo e aplicar limites mais restritos a endpoints específicos
# sem criar import circular com este módulo.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# allow_origins=["*"] (usado até aqui) é incompatível com allow_credentials=True,
# exigido pelo cookie httpOnly de sessão do login Google — o browser rejeita
# essa combinação. Sem FRONTEND_ORIGIN configurado (caso comum: a SPA é
# servida pelo próprio FastAPI, mesma origem, sem precisar de CORS), a lista
# fica vazia — nenhuma origem cross-site é liberada.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin] if settings.frontend_origin else [],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", settings.api_key_name],
)

app.include_router(auth.router)
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


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}


# SPA (frontend/, Vite+React) — servida só se o build (`npm run build`,
# gerando frontend/dist/) existir. Sem build (dev/test rodando só a API, ou
# antes da Fase 2 deste projeto), "/" continua sendo o health-check JSON de
# sempre — nenhuma mudança de comportamento nesse caso.
#
# Precisa vir depois de todos os app.include_router() acima — o catch-all
# abaixo bate com qualquer caminho, então se fosse registrado antes ele
# capturaria também as rotas de API.
#
# StaticFiles(html=True) sozinho NÃO faz o que parece: ele só serve
# index.html para o caminho raiz ou para diretórios reais, não para
# qualquer rota desconhecida — uma navegação direta do browser para
# /faturamento (rota client-side da SPA, sem ser uma chamada de API) daria
# 404 em vez de carregar a SPA. Por isso: StaticFiles só para /assets
# (arquivos com hash no nome, geridos pelo Vite) e um catch-all próprio que
# serve o arquivo estático se ele existir (ex.: /logo.jpg, copiado de
# frontend/public/ para a raiz do build) ou cai em index.html caso
# contrário — é o index.html carregado que faz o React Router decidir, no
# browser, o que renderizar para /faturamento, /cargas etc.
_frontend_dist = (Path(__file__).resolve().parent.parent / "frontend" / "dist").resolve()
if _frontend_dist.is_dir():
    _frontend_assets = _frontend_dist / "assets"
    if _frontend_assets.is_dir():
        app.mount("/assets", StaticFiles(directory=_frontend_assets), name="spa-assets")

    @app.get("/{caminho:path}", tags=["Health"], include_in_schema=False)
    def spa(caminho: str):
        # `caminho` vem da URL — resolve e confirma que o resultado continua
        # dentro de _frontend_dist antes de servir, para não abrir um path
        # traversal (ex.: /../../app/config.py) através deste catch-all.
        candidato = (_frontend_dist / caminho).resolve()
        if caminho and candidato.is_file() and candidato.is_relative_to(_frontend_dist):
            return FileResponse(candidato)
        return FileResponse(_frontend_dist / "index.html")
else:
    @app.get("/", tags=["Health"])
    def raiz():
        return {"nome": "RestDataAPI", "status": "online"}
