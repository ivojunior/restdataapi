from datetime import date
from typing import List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.database import get_db
from app.excel.estoque import gerar_excel_estoque
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


def _montar_items(linhas) -> List[SaldoEstoqueRead]:
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
    return items


def _filtrar_items(
    items: List[SaldoEstoqueRead], filial: Optional[str], codigo: Optional[str],
    descricao: Optional[str],
) -> List[SaldoEstoqueRead]:
    """Filtros locais equivalentes aos do client desktop (filial exata,
    código e descrição por substring case-insensitive) — só para a
    exportação bater com o que o usuário está vendo filtrado na tela, não
    filtros de negócio da consulta."""
    if filial:
        items = [item for item in items if item.filial == filial]
    if codigo:
        termo = codigo.lower()
        items = [item for item in items if termo in item.codigo_produto.lower()]
    if descricao:
        termo = descricao.lower()
        items = [item for item in items if termo in (item.descricao_produto or "").lower()]
    return items


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

    return {"skip": skip, "limit": limit, "items": _montar_items(linhas)}


@router.get("/export")
def exportar_saldos_estoque(
    tipo_produto: Optional[str] = None,
    local: Optional[str] = None,
    filial: Optional[str] = Query(
        None, description="Filtra pela filial exata (aplicado após a consulta, não em SQL).",
    ),
    codigo: Optional[str] = Query(
        None, description="Filtra pelo código do produto (contém, case-insensitive; "
        "aplicado após a consulta, não em SQL).",
    ),
    descricao: Optional[str] = Query(
        None, description="Filtra pela descrição do produto (contém, case-insensitive; "
        "aplicado após a consulta, não em SQL).",
    ),
    db: Session = Depends(get_db),
):
    """Gera a planilha .xlsx do recorte inteiro (sem paginação — réplica do
    client desktop, que carrega tudo antes de exportar)."""
    query = _query_saldos_estoque(db, tipo_produto, local)
    linhas = query.order_by(SaldoEstoque.filial, SaldoEstoque.codigo_produto).all()
    items = _filtrar_items(_montar_items(linhas), filial, codigo, descricao)

    planilha = gerar_excel_estoque(items)
    nome_arquivo = f"saldo_estoque_{date.today().strftime('%Y%m%d')}.xlsx"
    return StreamingResponse(
        planilha,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nome_arquivo}"'},
    )
