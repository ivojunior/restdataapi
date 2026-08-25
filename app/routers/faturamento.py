from datetime import date
from typing import Optional

from sqlalchemy import Integer, and_, case, func, literal_column
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
    # select_faturamento.sql agrega em duas camadas, e replicamos a mesma
    # estrutura (em vez de agregar tudo de uma vez): a subconsulta interna
    # calcula, por linha de SD2070, a quantidade (QTDE — sempre
    # D2_QUANT/B1_CONV, inclusive para bonificação; a consulta original não
    # zera a quantidade), o faturamento (FATURAMENTO — zero para
    # bonificação, D2_TOTAL só para venda: dar um produto de bonificação não
    # gera receita, mas continua contando na quantidade movimentada) e o
    # lucro bruto (D2_TOTAL - D2_CUSTO1, sempre, sem CASE — usa o D2_TOTAL
    # bruto mesmo para bonificação); a consulta externa soma tudo por
    # filial/dia/produto. DIA é DAY(D2_EMISSAO) — dia do mês, não uma data
    # completa: se o período (data_inicial/data_final) atravessar mais de um
    # mês, dias iguais de meses diferentes somam juntos no mesmo grupo,
    # exatamente como a consulta original faz.
    # literal_column("7")/("2") em vez de inteiros Python simples: o
    # SQLAlchemy compilaria 7 e 2 como parâmetros ligados (?), e cada
    # ocorrência desta expressão no SQL final (uma na lista de colunas, outra
    # no GROUP BY) ganharia parâmetros ? diferentes — mesmo sendo o mesmo
    # objeto Python reutilizado. O SQL Server então não consegue provar
    # estaticamente que os dois SUBSTRING(col, ?, ?) são a mesma expressão e
    # rejeita a query ("D2_EMISSAO is invalid in the select list because it
    # is not contained in either an aggregate function or the GROUP BY
    # clause"). Com literal_column, 7 e 2 viram texto SQL fixo em vez de
    # parâmetro, então as duas ocorrências ficam byte-a-byte idênticas e o
    # SQL Server reconhece a mesma expressão nas duas cláusulas. Não
    # reproduzido no SQLite dos testes, que é mais permissivo nessa
    # validação — não confiar só nos testes pra esse tipo de expressão
    # calculada usada como chave de agrupamento; testar contra o SQL Server
    # real (ou pelo menos inspecionar o SQL compilado) antes de assumir que
    # está correto.
    dia_coluna = func.cast(
        func.substring(ItemFaturamento.emissao, literal_column("7"), literal_column("2")),
        Integer,
    )

    # Sem CASE — diferente de uma versão anterior desta query, que zerava a
    # quantidade para bonificação. Agora a quantidade conta sempre; é o
    # faturamento (abaixo) que zera para bonificação.
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
            # PRECO_MEDIO já é um AVG() dentro da subconsulta original — o
            # GROUP BY interno agrupa por praticamente todas as colunas
            # diferenciadoras, então normalmente é a razão de uma única
            # linha; preservado como AVG() para bater exatamente com
            # select_faturamento.sql, caso existam linhas com os mesmos
            # valores em SD2070.
            func.avg(
                ItemFaturamento.total / (ItemFaturamento.quantidade / Produto.conversao)
            ).label("preco_medio"),
            (ItemFaturamento.total - ItemFaturamento.custo).label("lucro_bruto"),
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
            # Diferente da consulta original (DATA_INICIO/DATA_FIM fixos via
            # bind params), aqui o período é parametrizável via query string:
            # sem data_inicial, assume a data atual do sistema — mesmo
            # padrão já usado em /cargas e /financeiro.
            ItemFaturamento.emissao >= data_inicial,
        )
        .group_by(
            ItemFaturamento.filial,
            dia_coluna,
            ItemFaturamento.codigo_produto,
            Produto.descricao,
            ItemFaturamento.operacao,
            ItemFaturamento.quantidade,
            Produto.conversao,
            ItemFaturamento.total,
            ItemFaturamento.custo,
        )
    )
    if data_final:
        inner = inner.filter(ItemFaturamento.emissao <= data_final)

    tmp = inner.subquery()

    # ATENÇÃO: margem divide por SUM(faturamento) sem proteção contra zero —
    # igual à consulta original. Agora que faturamento é zerado para
    # bonificação (veja faturamento_coluna acima), um grupo (filial/dia/
    # produto) com só bonificação e nenhuma venda no período sempre tem
    # faturamento total zero — mais fácil de acontecer na prática do que
    # antes. Nesse caso o SQL Server lança "Divide by zero error" e a
    # requisição falha com 500.
    # Réplica fiel do comportamento original; não adicionamos proteção sem
    # confirmação de que isso é desejado.
    return (
        db.query(
            tmp.c.filial,
            tmp.c.dia,
            tmp.c.codigo,
            tmp.c.descricao,
            func.sum(tmp.c.qtde).label("qtde"),
            func.sum(tmp.c.faturamento).label("faturamento"),
            func.avg(tmp.c.preco_medio).label("preco_medio"),
            func.sum(tmp.c.lucro_bruto).label("lucro_bruto"),
            (func.sum(tmp.c.lucro_bruto) / func.sum(tmp.c.faturamento) * 100).label("margem"),
        )
        .group_by(tmp.c.filial, tmp.c.dia, tmp.c.codigo, tmp.c.descricao)
        .order_by(tmp.c.filial, tmp.c.dia, tmp.c.codigo)
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
            faturamento=faturamento,
            preco_medio=preco_medio,
            lucro_bruto=lucro_bruto,
            margem=margem,
        )
        for (
            filial, dia, codigo, descricao, qtde, faturamento,
            preco_medio, lucro_bruto, margem,
        ) in linhas
    ]

    return {"skip": skip, "limit": limit, "items": items}
