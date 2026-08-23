import enum
from datetime import date
from typing import Optional

from sqlalchemy import and_, func, not_, or_
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
    # Ver comentário equivalente em app/crud/base.py: with_entities evita que
    # o count() embrulhe a query original (com os joins em Fornecedor/
    # TipoOperacao) numa subquery desnecessária.
    total = query.with_entities(func.count()).order_by(None).scalar()
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
