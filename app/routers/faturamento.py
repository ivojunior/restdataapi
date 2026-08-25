from datetime import date
from typing import Optional

from sqlalchemy import Integer, and_, case, func
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.models.item_faturamento import ItemFaturamento
from app.models.produto import Produto
from app.schemas.common import PaginatedResponse
from app.schemas.faturamento import FaturamentoRead
from app.security import verify_api_key

router = APIRouter(
    prefix="/faturamento",
    tags=["Faturamento"],
    dependencies=[Depends(verify_api_key)],
)

# Regras de negócio fixas do relatório (réplica de select_faturamento.sql):
# só produtos acabados (B1_TIPO = 'PA') e só estes tipos de operação — '501'
# é venda; '542'/'543'/'544' são bonificações (customização desta instalação
# do Protheus, sem lista pública de valores, confirmada pelo usuário — o
# comentário "-- bonificacoes" na consulta original chegou a ser corrigido
# pelo usuário; antes achávamos, por engano, que eram devoluções).
_TIPO_PRODUTO = "PA"
_OPERACOES = ("501", "542", "543", "544")
_OPERACOES_BONIFICACAO = ("542", "543", "544")
_OPERACAO_VENDA = "501"


def _query_faturamento(db: Session, data_inicial: str, data_final: Optional[str] = None):
    # select_faturamento.sql não agrega mais em duas camadas: a subconsulta
    # interna agora é uma projeção linha a linha de SD2070 (sem GROUP BY),
    # calculando só a quantidade (QTDE — sempre D2_QUANT/B1_CONV, inclusive
    # para bonificação; nunca zerada), o faturamento (FATURAMENTO — zero
    # para bonificação, D2_TOTAL só para venda: dar um produto de
    # bonificação não gera receita, mas continua contando na quantidade
    # movimentada) e o custo (CUSTO — D2_CUSTO1 puro, sem SUM: não há mais
    # agregação nenhuma nesta camada). É a consulta externa quem soma tudo
    # por filial/dia/produto e só então deriva PRECO_MEDIO (SUM(FATURAMENTO)
    # / SUM(QTDE) — média ponderada pela quantidade, não mais a média simples
    # de uma razão por linha) e LUCRO_BRUTO (SUM(FATURAMENTO) - SUM(CUSTO)) a
    # partir do FATURAMENTO já zerado para bonificação. DIA é DAY(D2_EMISSAO)
    # — dia do mês, não uma data completa: se o período (data_inicial/
    # data_final) atravessar mais de um mês, dias iguais de meses diferentes
    # somam juntos no mesmo grupo, exatamente como a consulta original faz.
    #
    # DIA usa CAST(SUBSTRING(D2_EMISSAO, 7, 2) AS INTEGER) com 7 e 2 como
    # inteiros Python normais (não literal_column, como em versões
    # anteriores deste endpoint): aquele workaround só era necessário porque
    # a mesma expressão aparecia duas vezes no SQL final (na lista de
    # colunas e no GROUP BY da camada interna), e o SQL Server exige texto
    # byte-a-byte idêntico nas duas ocorrências para validar o GROUP BY. Sem
    # GROUP BY na camada interna, a expressão aparece só uma vez — o
    # problema não existe mais nesta versão da consulta.
    dia_coluna = func.cast(func.substring(ItemFaturamento.emissao, 7, 2), Integer)

    # Sem CASE — a quantidade conta sempre; é o faturamento (abaixo) que
    # zera para bonificação.
    qtde_coluna = ItemFaturamento.quantidade / Produto.conversao

    faturamento_coluna = case(
        (ItemFaturamento.operacao.in_(_OPERACOES_BONIFICACAO), 0),
        (ItemFaturamento.operacao == _OPERACAO_VENDA, ItemFaturamento.total),
        else_=0,
    )

    inner = (
        db.query(
            ItemFaturamento.filial.label("filial"),
            dia_coluna.label("dia"),
            ItemFaturamento.codigo_produto.label("codigo"),
            Produto.descricao.label("descricao"),
            qtde_coluna.label("qtde"),
            faturamento_coluna.label("faturamento"),
            ItemFaturamento.custo.label("custo"),
        )
        .join(
            Produto,
            and_(
                Produto.deletado != "*",
                Produto.filial == "  ",
                Produto.codigo == ItemFaturamento.codigo_produto,
                Produto.tipo == _TIPO_PRODUTO,
            ),
        )
        .filter(
            ItemFaturamento.deletado != "*",
            ItemFaturamento.operacao.in_(_OPERACOES),
            # Diferente da consulta original (DATA_INICIAL/DATA_FINAL fixos
            # via bind params), aqui o período é parametrizável via query
            # string: sem data_inicial, assume a data atual do sistema —
            # mesmo padrão já usado em /cargas e /financeiro.
            ItemFaturamento.emissao >= data_inicial,
        )
    )
    if data_final:
        inner = inner.filter(ItemFaturamento.emissao <= data_final)

    tmp = inner.subquery()

    # ATENÇÃO: preco_medio e margem_bruta dividem por SUM(qtde)/SUM(faturamento)
    # sem proteção contra zero — igual à consulta original. Um grupo
    # (filial/dia/produto) com só bonificação e nenhuma venda no período
    # sempre tem faturamento total zero; um grupo cuja soma de QTDE dê zero
    # também é possível em tese (item com D2_QUANT zerado). Em qualquer um
    # desses casos o SQL Server lança "Divide by zero error" e a requisição
    # falha com 500. Réplica fiel do comportamento original; não adicionamos
    # proteção sem confirmação de que isso é desejado.
    faturamento_expr = func.sum(tmp.c.faturamento)
    lucro_bruto_expr = faturamento_expr - func.sum(tmp.c.custo)
    return (
        db.query(
            tmp.c.filial,
            tmp.c.dia,
            tmp.c.codigo,
            tmp.c.descricao,
            func.sum(tmp.c.qtde).label("qtde"),
            (faturamento_expr / func.sum(tmp.c.qtde)).label("preco_medio"),
            faturamento_expr.label("faturamento"),
            func.sum(tmp.c.custo).label("custo"),
            lucro_bruto_expr.label("lucro_bruto"),
            (lucro_bruto_expr / faturamento_expr * 100).label("margem_bruta"),
        )
        .group_by(tmp.c.filial, tmp.c.dia, tmp.c.codigo, tmp.c.descricao)
        .order_by(tmp.c.filial, tmp.c.dia, tmp.c.codigo, tmp.c.descricao)
    )


@router.get("/", response_model=PaginatedResponse[FaturamentoRead])
def listar_faturamento(
    skip: int = 0,
    limit: int = Query(50, le=200),
    data_inicial: Optional[str] = Query(
        None,
        description="Data mínima de emissão, formato AAAAMMDD (D2_EMISSAO >= data_inicial). "
        "Sem o parâmetro, assume a data atual do sistema.",
    ),
    data_final: Optional[str] = Query(
        None,
        description="Data máxima de emissão, formato AAAAMMDD (D2_EMISSAO <= data_final). "
        "Sem o parâmetro, não há limite superior.",
    ),
    db: Session = Depends(get_db),
):
    data_filtro = data_inicial or date.today().strftime("%Y%m%d")
    linhas = (
        _query_faturamento(db, data_filtro, data_final)
        .offset(skip)
        .limit(limit)
        .all()
    )

    items = [
        FaturamentoRead(
            filial=filial,
            dia=dia,
            codigo=codigo,
            descricao=descricao,
            quantidade=qtde,
            preco_medio=preco_medio,
            faturamento=faturamento,
            custo=custo,
            lucro_bruto=lucro_bruto,
            margem_bruta=margem_bruta,
        )
        for (
            filial, dia, codigo, descricao, qtde, preco_medio,
            faturamento, custo, lucro_bruto, margem_bruta,
        ) in linhas
    ]

    return {"skip": skip, "limit": limit, "items": items}
