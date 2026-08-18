from sqlalchemy import and_
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.models.fornecedor import Fornecedor
from app.models.tipo_operacao import TipoOperacao
from app.models.titulo_pagar import TituloPagar
from app.schemas.common import PaginatedResponse
from app.schemas.financeiro import FinanceiroRead
from app.security import verify_api_key

router = APIRouter(
    prefix="/financeiro",
    tags=["Financeiro"],
    dependencies=[Depends(verify_api_key)],
)

# Regras de negócio fixas do relatório (replicam select_financeiro.sql):
# considera apenas títulos com vencimento real a partir desta data e exclui
# os tipos de lançamento PA/PR/NDF.
_VENCIMENTO_MINIMO = "20260301"
_TIPOS_EXCLUIDOS = ("PA", "PR", "NDF")


def _query_financeiro(db: Session):
    return (
        db.query(TituloPagar, TipoOperacao.descricao)
        .join(
            Fornecedor,
            and_(
                Fornecedor.deletado != "*",
                Fornecedor.filial == "  ",
                Fornecedor.codigo == TituloPagar.fornecedor,
                Fornecedor.loja == TituloPagar.loja,
            ),
        )
        .outerjoin(
            TipoOperacao,
            and_(
                TipoOperacao.deletado != "*",
                TipoOperacao.filial == "  ",
                TipoOperacao.codigo == TituloPagar.codigo_operacao,
            ),
        )
        .filter(
            TituloPagar.deletado != "*",
            TituloPagar.vencimento_real >= _VENCIMENTO_MINIMO,
            TituloPagar.tipo.notin_(_TIPOS_EXCLUIDOS),
        )
    )


@router.get("/", response_model=PaginatedResponse[FinanceiroRead])
def listar_financeiro(
    skip: int = 0,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    query = _query_financeiro(db)
    total = query.count()
    # order_by aplicado apenas aqui (após o count()): o MSSQL exige ORDER BY
    # junto de OFFSET/LIMIT, mas não aceita ORDER BY dentro da subquery que o
    # SQLAlchemy gera para count() quando não há TOP/OFFSET nela.
    linhas = query.order_by(TituloPagar.rec_no).offset(skip).limit(limit).all()

    items = []
    for titulo, descricao_operacao in linhas:
        item = FinanceiroRead.model_validate(titulo)
        item.descricao_operacao = descricao_operacao
        items.append(item)

    return {"total": total, "skip": skip, "limit": limit, "items": items}
