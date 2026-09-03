import enum
from datetime import date
from typing import List, Optional

from sqlalchemy import and_, func, not_, or_
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.database import get_db
from app.excel.categorizacao_financeiro import categorizar
from app.excel.financeiro import gerar_excel_financeiro
from app.models.fornecedor import Fornecedor
from app.models.tipo_operacao import TipoOperacao
from app.models.titulo_pagar import TituloPagar
from app.schemas.common import PaginatedResponse
from app.schemas.financeiro import FinanceiroRead
from app.security import verify_api_key_or_session

router = APIRouter(
    prefix="/financeiro",
    tags=["Financeiro"],
    dependencies=[Depends(verify_api_key_or_session)],
)

# Regra de negócio fixa do relatório (réplica de select_financeiro.sql): exclui
# os tipos de lançamento PA/PR/NDF. O período de vencimento não é mais fixo —
# é parametrizável via query string (vencimento_de/vencimento_ate).
_TIPOS_EXCLUIDOS = ("PA", "PR", "NDF")


class StatusFinanceiro(str, enum.Enum):
    """Mesma classificação já usada nos clients desktop (veja _status_from_row):
    baixado tem prioridade sobre vencido, que por sua vez depende da data atual."""

    em_aberto = "em_aberto"
    vencido = "vencido"
    baixado = "baixado"


def _sem_baixa(coluna):
    """E2_BAIXA é CHAR(8) do Protheus: 'sem baixa' pode vir como NULL, string
    vazia ou só espaços — nunca apenas `coluna == ""`."""
    return or_(coluna.is_(None), func.ltrim(func.rtrim(coluna)) == "")


def _query_financeiro(
    db: Session,
    vencimento_de: str,
    vencimento_ate: Optional[str],
    status: Optional[StatusFinanceiro] = None,
):
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

    if status == StatusFinanceiro.baixado:
        query = query.filter(not_(_sem_baixa(TituloPagar.data_baixa)))
    elif status == StatusFinanceiro.vencido:
        hoje = date.today().strftime("%Y%m%d")
        query = query.filter(
            _sem_baixa(TituloPagar.data_baixa),
            TituloPagar.vencimento_real < hoje,
        )
    elif status == StatusFinanceiro.em_aberto:
        hoje = date.today().strftime("%Y%m%d")
        query = query.filter(
            _sem_baixa(TituloPagar.data_baixa),
            TituloPagar.vencimento_real >= hoje,
        )
    return query


def _montar_items(linhas) -> List[FinanceiroRead]:
    items = []
    for titulo, descricao_operacao in linhas:
        item = FinanceiroRead.model_validate(titulo)
        item.descricao_operacao = descricao_operacao
        # Réplica de select_financeiro.sql: "valor" não é mais E2_VALOR puro,
        # e sim a soma dele com as retenções/tributos do título. `or 0` cobre
        # títulos com essas colunas nulas (no SQL Server, NULL + número
        # resultaria em NULL — aqui tratamos como 0 para não quebrar `valor`,
        # que a API sempre expôs como não-nulo).
        item.valor = (
            titulo.valor
            + (titulo.irrf or 0)
            + (titulo.csll or 0)
            + (titulo.pis or 0)
            + (titulo.cofins or 0)
        )
        items.append(item)
    return items


def _filtrar_items(
    items: List[FinanceiroRead], filial: Optional[str], fornecedor: Optional[str],
    tipo: Optional[str], tipo_operacao: Optional[str], categoria: Optional[str],
) -> List[FinanceiroRead]:
    """Filtros locais equivalentes aos do client desktop (filial exata, tipo
    exato — case-insensitive —, fornecedor/tipo de operação por substring —
    case-insensitive —, categoria exata) — só para a exportação bater com o
    que o usuário está vendo filtrado na tela, não filtros de negócio da
    consulta. `categoria` não vem do banco (ver categorizacao_financeiro.py),
    então esse filtro recalcula a categoria de cada item para comparar."""
    if filial:
        items = [item for item in items if item.filial == filial]
    if fornecedor:
        termo = fornecedor.lower()
        items = [item for item in items if termo in (item.nome_fornecedor or "").lower()]
    if tipo:
        termo = tipo.upper()
        items = [item for item in items if (item.tipo or "").upper() == termo]
    if tipo_operacao:
        termo = tipo_operacao.lower()
        items = [
            item for item in items
            if termo in (item.descricao_operacao or "").lower()
        ]
    if categoria:
        items = [
            item for item in items
            if categorizar(item.nome_fornecedor, item.historico) == categoria
        ]
    return items


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
    status: Optional[StatusFinanceiro] = Query(
        None,
        description="Filtra pelo status do título: 'em_aberto' (sem data de baixa e "
        "vencimento_real >= hoje), 'vencido' (sem data de baixa e vencimento_real < hoje) "
        "ou 'baixado' (com data de baixa preenchida). Sem o parâmetro, não filtra por status. "
        "Como vencimento_de já começa em hoje por padrão, para ver títulos vencidos ajuste "
        "vencimento_de para uma data anterior.",
    ),
    db: Session = Depends(get_db),
):
    data_de = vencimento_de or date.today().strftime("%Y%m%d")
    query = _query_financeiro(db, data_de, vencimento_ate, status)
    linhas = query.order_by(TituloPagar.rec_no).offset(skip).limit(limit).all()

    return {"skip": skip, "limit": limit, "items": _montar_items(linhas)}


@router.get("/export")
def exportar_financeiro(
    vencimento_de: Optional[str] = Query(
        None, description="Data mínima de vencimento, formato AAAAMMDD. Sem o parâmetro, "
        "assume a data atual do sistema.",
    ),
    vencimento_ate: Optional[str] = Query(
        None, description="Data máxima de vencimento, formato AAAAMMDD.",
    ),
    status: Optional[StatusFinanceiro] = None,
    filial: Optional[str] = Query(
        None, description="Filtra pela filial exata (aplicado após a consulta, não em SQL).",
    ),
    fornecedor: Optional[str] = Query(
        None, description="Filtra pelo nome do fornecedor (contém, case-insensitive; "
        "aplicado após a consulta, não em SQL).",
    ),
    tipo: Optional[str] = Query(
        None, description="Filtra pelo tipo de título exato (case-insensitive; aplicado "
        "após a consulta, não em SQL).",
    ),
    tipo_operacao: Optional[str] = Query(
        None, description="Filtra pela descrição do tipo de operação (contém, "
        "case-insensitive; aplicado após a consulta, não em SQL).",
    ),
    categoria: Optional[str] = Query(
        None, description="Filtra pela categoria calculada do título (ver "
        "app/excel/categorizacao_financeiro.py; aplicado após a consulta, não em SQL).",
    ),
    db: Session = Depends(get_db),
):
    """Gera a planilha .xlsx do período inteiro (sem paginação — réplica do
    client desktop, que carrega tudo antes de exportar)."""
    data_de = vencimento_de or date.today().strftime("%Y%m%d")
    query = _query_financeiro(db, data_de, vencimento_ate, status)
    linhas = query.order_by(TituloPagar.rec_no).all()
    items = _filtrar_items(
        _montar_items(linhas), filial, fornecedor, tipo, tipo_operacao, categoria)

    planilha = gerar_excel_financeiro(items)
    nome_arquivo = f"financeiro_{date.today().strftime('%Y%m%d')}.xlsx"
    return StreamingResponse(
        planilha,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nome_arquivo}"'},
    )
