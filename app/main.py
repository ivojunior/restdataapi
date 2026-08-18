import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger("restdataapi")

from app.routers import financeiro, fornecedores, produtos, saldos_estoque, titulos_pagar

app = FastAPI(
    title="RestDataAPI",
    description="API REST para acesso a dados do Protheus.",
    version="1.0.0",
)

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
