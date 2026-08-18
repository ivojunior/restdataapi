from datetime import date
from typing import Optional

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

# Regra de negócio fixa do relatório (réplica de select_financeiro.sql): exclui
# os tipos de lançamento PA/PR/NDF. O período de vencimento não é mais fixo —
# é parametrizável via query string (vencimento_de/vencimento_ate).
_TIPOS_EXCLUIDOS = ("PA", "PR", "NDF")


def _query_financeiro(db: Session, vencimento_de: str, vencimento_ate: Optional[str]):
    query = (
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
            TituloPagar.vencimento_real >= vencimento_de,
            TituloPagar.tipo.notin_(_TIPOS_EXCLUIDOS),
        )
    )
    if vencimento_ate:
        query = query.filter(TituloPagar.vencimento_real <= vencimento_ate)
    return query


@router.get("/", response_model=PaginatedResponse[FinanceiroRead])
def listar_financeiro(
    skip: int = 0,
    limit: int = Query(50, le=200),
    vencimento_de: Optional[str] = Query(
        None,
        description="Data mínima de vencimento, formato AAAAMMDD (E2_VENCREA >= vencimento_de). "
        "Sem o parâmetro, assume a data atual do sistema.",
    ),
    vencimento_ate: Optional[str] = Query(
        None,
        description="Data máxima de vencimento, formato AAAAMMDD (E2_VENCREA <= vencimento_ate). "
        "Sem o parâmetro, não limita o vencimento máximo.",
    ),
    db: Session = Depends(get_db),
):
    data_de = vencimento_de or date.today().strftime("%Y%m%d")
    query = _query_financeiro(db, data_de, vencimento_ate)
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
