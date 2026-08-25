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
    # custo (CUSTO_MEDIO — SUM(D2_CUSTO1); a consulta externa soma tudo por
    # filial/dia/produto e só então calcula PRECO_MEDIO e LUCRO_BRUTO a
    # partir do FATURAMENTO já zerado, e não mais do D2_TOTAL bruto (correção
    # do usuário nesta consulta — antes o lucro bruto usava D2_TOTAL bruto
    # mesmo para bonificação, o que dava lucro positivo mesmo quando o
    # faturamento reportado era zero; agora bonificação sempre gera lucro
    # bruto negativo, igual ao custo do produto dado). DIA é DAY(D2_EMISSAO)
    # — dia do mês, não uma data completa: se o período (data_inicial/
    # data_final) atravessar mais de um mês, dias iguais de meses diferentes
    # somam juntos no mesmo grupo, exatamente como a consulta original faz.
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
            # SUM() em vez de referência direta à coluna: select_faturamento.sql
            # escreve como SUM(D2.D2_CUSTO1) mesmo D2_CUSTO1 já estando no
            # GROUP BY interno (logo, não há o que somar de fato — cada grupo
            # já corresponde a uma única combinação de valores). Preservado
            # como SUM() só para bater exatamente com a consulta original.
            func.sum(ItemFaturamento.custo).label("custo_medio"),
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

    # PRECO_MEDIO e LUCRO_BRUTO não vêm mais prontos da subconsulta interna
    # (que só expõe qtde/faturamento/custo_medio por linha): são calculados
    # aqui em cima, a partir do FATURAMENTO já zerado para bonificação — não
    # do D2_TOTAL bruto. Correção do usuário em select_faturamento.sql: antes
    # PRECO_MEDIO usava D2_TOTAL/QTDE e LUCRO_BRUTO usava D2_TOTAL-D2_CUSTO1,
    # os dois ignorando a zeragem de bonificação; agora ambos usam
    # TMP.FATURAMENTO (já zerado), então uma linha de bonificação contribui
    # com preço médio 0 e lucro bruto = -custo (prejuízo igual ao custo do
    # produto dado), consistente com o faturamento reportado como zero.
    #
    # ATENÇÃO: margem (e agora também preco_medio) dividem por
    # SUM(faturamento)/qtde sem proteção contra zero — igual à consulta
    # original. Um grupo (filial/dia/produto) com só bonificação e nenhuma
    # venda no período sempre tem faturamento total zero, e o SQL Server
    # lança "Divide by zero error" nesse caso, falhando a requisição com 500.
    # Réplica fiel do comportamento original; não adicionamos proteção sem
    # confirmação de que isso é desejado.
    lucro_bruto_expr = func.sum(tmp.c.faturamento - tmp.c.custo_medio)
    return (
        db.query(
            tmp.c.filial,
            tmp.c.dia,
            tmp.c.codigo,
            tmp.c.descricao,
            func.sum(tmp.c.qtde).label("qtde"),
            func.sum(tmp.c.faturamento).label("faturamento"),
            func.avg(tmp.c.faturamento / tmp.c.qtde).label("preco_medio"),
            lucro_bruto_expr.label("lucro_bruto"),
            (lucro_bruto_expr / func.sum(tmp.c.faturamento) * 100).label("margem"),
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
