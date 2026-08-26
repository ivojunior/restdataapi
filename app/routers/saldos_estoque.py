from typing import Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.models.produto import Produto
from app.models.saldo_estoque import SaldoEstoque
from app.schemas.common import PaginatedResponse
from app.schemas.saldo_estoque import SaldoEstoqueRead
from app.security import verify_api_key_or_session

router = APIRouter(
    prefix="/saldos-estoque",
    tags=["Saldo de Estoque"],
    dependencies=[Depends(verify_api_key_or_session)],
)


def _query_saldos_estoque(db: Session, tipo_produto: Optional[str], local: Optional[str]):
    # Seleciona apenas as colunas usadas pelo relatório (em vez da entidade
    # SaldoEstoque inteira): o model mapeia campos de SB2070 (ex.: B2_QPEDCOM)
    # que não existem em todas as instalações do Protheus, e não são usados
    # aqui — selecioná-los à toa quebra a query com "Invalid column name".
    query = (
        db.query(
            SaldoEstoque.filial,
            SaldoEstoque.local,
            SaldoEstoque.codigo_produto,
            SaldoEstoque.saldo_atual,
            SaldoEstoque.valor_atual,
            Produto.descricao,
            Produto.conversao,
        )
        .join(
            Produto,
            and_(
                Produto.deletado != "*",
                Produto.filial == "  ",
                Produto.codigo == SaldoEstoque.codigo_produto,
            ),
        )
        .filter(SaldoEstoque.deletado != "*", SaldoEstoque.saldo_atual > 0)
    )
    # Réplica de select_estoque_produtos.sql, mas com o tipo de produto (B1_TIPO)
    # e o armazém (B2_LOCAL) parametrizáveis via query string em vez de fixos —
    # o cliente decide qual recorte de estoque analisar (ex.: produtos acabados
    # "PA"/armazém "01" ou vasilhames "AM"/armazém "20").
    if tipo_produto:
        query = query.filter(Produto.tipo == tipo_produto)
    if local:
        query = query.filter(SaldoEstoque.local == local)
    return query


@router.get("/", response_model=PaginatedResponse[SaldoEstoqueRead])
def listar_saldos_estoque(
    skip: int = 0,
    limit: int = Query(50, le=200),
    tipo_produto: Optional[str] = None,
    local: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = _query_saldos_estoque(db, tipo_produto, local)
    linhas = (
        query.order_by(SaldoEstoque.filial, SaldoEstoque.codigo_produto)
        .offset(skip)
        .limit(limit)
        .all()
    )

    items = []
    for filial, local_armazem, codigo_produto, saldo_atual, valor_atual, descricao_produto, conversao in linhas:
        quantidade = (saldo_atual / conversao) if conversao else saldo_atual
        items.append(SaldoEstoqueRead(
            filial=filial,
            local=local_armazem,
            codigo_produto=codigo_produto,
            descricao_produto=descricao_produto,
            quantidade=quantidade,
            valor_atual=valor_atual,
        ))

    return {"skip": skip, "limit": limit, "items": items}
