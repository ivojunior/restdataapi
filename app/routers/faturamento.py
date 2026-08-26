from datetime import date
from typing import List, Optional

from sqlalchemy import Integer, Numeric, and_, case, cast, func
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.database import get_db
from app.excel.faturamento import gerar_excel_faturamento
from app.models.item_faturamento import ItemFaturamento
from app.models.produto import Produto
from app.schemas.common import PaginatedResponse
from app.schemas.faturamento import FaturamentoRead
from app.security import verify_api_key_or_session

router = APIRouter(
    prefix="/faturamento",
    tags=["Faturamento"],
    dependencies=[Depends(verify_api_key_or_session)],
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

    # preco_medio, margem e markup dividem por SUM(qtde)/SUM(faturamento)/
    # SUM(custo) — um grupo (filial/dia/produto) com só bonificação e nenhuma
    # venda no período sempre tem faturamento total zero; um grupo cuja soma
    # de QTDE ou de CUSTO dê zero também é possível em tese (item com
    # D2_QUANT ou D2_CUSTO1 zerado). A consulta original (SQL Server) lança
    # "Divide by zero error" nesse caso — risco que era só teórico até
    # aparecer de verdade num teste manual da SPA (piloto de Faturamento):
    # um dia com só bonificação de um produto, sem nenhuma venda no mesmo
    # grupo, gerou 500. func.nullif(x, 0) troca o denominador por NULL
    # quando ele é zero — SQL Server e SQLite concordam no resultado (NULL,
    # não erro), e os três campos ficam Optional no schema (None = "não é
    # possível calcular essa razão para este grupo", não "zero").
    #
    # cast(..., Numeric(p, s)) explícito em cada denominador: sem isso, o
    # SQL Server compila CAST(NULLIF(...) AS NUMERIC) — sem precisão/escala
    # — que por padrão vira NUMERIC(18, 0), truncando os três resultados
    # para inteiro (sem casas decimais nenhuma). Antes do NULLIF, o
    # SQLAlchemy inferia a precisão automaticamente a partir da coluna
    # original; envolver em NULLIF quebrou essa inferência — só percebido
    # comparando o SQL compilado antes/depois de adicionar o NULLIF, não
    # pelos testes (SQLite não tem essa armadilha de escala padrão do CAST).
    faturamento_expr = func.sum(tmp.c.faturamento)
    custo_expr = func.sum(tmp.c.custo)
    qtde_expr = func.sum(tmp.c.qtde)
    lucro_bruto_expr = faturamento_expr - custo_expr
    return (
        db.query(
            tmp.c.filial,
            tmp.c.dia,
            tmp.c.codigo,
            tmp.c.descricao,
            qtde_expr.label("qtde"),
            (faturamento_expr / cast(func.nullif(qtde_expr, 0), Numeric(18, 4))).label("preco_medio"),
            faturamento_expr.label("faturamento"),
            custo_expr.label("custo"),
            lucro_bruto_expr.label("lucro_bruto"),
            # MARGEM: lucro bruto sobre o faturamento. MARKUP: lucro bruto
            # sobre o custo — mesmo numerador (lucro_bruto_expr), denominador
            # diferente; são métricas relacionadas mas não intercambiáveis
            # (margem nunca chega a 100%, markup não tem teto).
            # (18, 2), não (18, 4) como preco_medio acima: faturamento_expr/
            # custo_expr somam colunas Numeric(18, 2) (D2_TOTAL/D2_CUSTO1),
            # enquanto qtde_expr soma uma coluna Numeric(18, 4) — a escala do
            # cast replica a escala "natural" de cada denominador, não um
            # valor arbitrário igual para os três.
            (lucro_bruto_expr / cast(func.nullif(faturamento_expr, 0), Numeric(18, 2)) * 100).label("margem"),
            (lucro_bruto_expr / cast(func.nullif(custo_expr, 0), Numeric(18, 2)) * 100).label("markup"),
        )
        .group_by(tmp.c.filial, tmp.c.dia, tmp.c.codigo, tmp.c.descricao)
        .order_by(tmp.c.filial, tmp.c.dia, tmp.c.codigo, tmp.c.descricao)
    )


def _montar_items(linhas) -> List[FaturamentoRead]:
    return [
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
            margem=margem,
            markup=markup,
        )
        for (
            filial, dia, codigo, descricao, qtde, preco_medio,
            faturamento, custo, lucro_bruto, margem, markup,
        ) in linhas
    ]


def _filtrar_items(
    items: List[FaturamentoRead], filial: Optional[str], produto: Optional[str],
) -> List[FaturamentoRead]:
    """Filtros locais equivalentes aos do client desktop (filial exata,
    produto por código OU descrição, case-insensitive) — aplicados aqui em
    Python, não em SQL, porque só existem para a exportação bater com o que
    o usuário está vendo filtrado na tela, não como filtro de negócio."""
    if filial:
        items = [item for item in items if item.filial == filial]
    if produto:
        termo = produto.lower()
        items = [
            item for item in items
            if termo in item.codigo.lower() or termo in (item.descricao or "").lower()
        ]
    return items


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

    return {"skip": skip, "limit": limit, "items": _montar_items(linhas)}


@router.get("/export")
def exportar_faturamento(
    data_inicial: Optional[str] = Query(
        None,
        description="Data mínima de emissão, formato AAAAMMDD. Sem o parâmetro, assume a "
        "data atual do sistema.",
    ),
    data_final: Optional[str] = Query(
        None, description="Data máxima de emissão, formato AAAAMMDD.",
    ),
    filial: Optional[str] = Query(
        None, description="Filtra pela filial exata (aplicado após a consulta, não em SQL).",
    ),
    produto: Optional[str] = Query(
        None,
        description="Filtra por código ou descrição do produto (contém, case-insensitive; "
        "aplicado após a consulta, não em SQL).",
    ),
    db: Session = Depends(get_db),
):
    """Gera a planilha .xlsx do período (sem paginação — sempre exporta o
    recorte inteiro, réplica do que o client desktop faz ao carregar tudo
    antes de exportar). `filial`/`produto` existem só para a exportação
    bater com o que o usuário está vendo filtrado na tela da SPA — o
    endpoint de listagem (`GET /faturamento/`) não tem esses parâmetros
    porque lá o filtro é sempre local ao client, nunca enviado à API."""
    data_filtro = data_inicial or date.today().strftime("%Y%m%d")
    linhas = _query_faturamento(db, data_filtro, data_final).all()
    items = _filtrar_items(_montar_items(linhas), filial, produto)

    planilha = gerar_excel_faturamento(items)
    nome_arquivo = f"faturamento_{data_filtro[:6]}.xlsx"
    return StreamingResponse(
        planilha,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nome_arquivo}"'},
    )
