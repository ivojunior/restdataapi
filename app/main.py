from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

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
    return JSONResponse(status_code=500, content={"detail": "Erro ao acessar o banco de dados"})


@app.get("/", tags=["Health"])
def raiz():
    return {"nome": "RestDataAPI", "status": "online"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
