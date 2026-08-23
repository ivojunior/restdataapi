import enum
from datetime import date
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.models.cliente import Cliente
from app.models.item_carga import ItemCarga
from app.models.nota_fiscal_saida import NotaFiscalSaida
from app.models.veiculo_carga import VeiculoCarga
from app.schemas.carga import CargaRead
from app.schemas.common import PaginatedResponse
from app.security import verify_api_key

router = APIRouter(
    prefix="/cargas",
    tags=["Cargas"],
    dependencies=[Depends(verify_api_key)],
)

# Regra de negócio fixa do relatório (réplica de select_cargas.sql): sequência
# '999999' é a convenção do Protheus para item de carga cancelado.
_SEQUENCIA_CANCELADA = "999999"


# Códigos de DAK_ACECAR (customização desta instalação do Protheus, sem
# lista pública de valores — confirmados pelo usuário) considerados
# "fechados". Qualquer outro código é considerado "aberto".
_STATUS_CARGA_FECHADOS = ("7", "8")


class StatusCargaFiltro(str, enum.Enum):
    """Classificação do status da carga (DAK_ACECAR) em apenas 2 tipos:
    "encerrada" (códigos 7 e 8) ou "aberta" (demais códigos)."""

    aberta = "aberta"
    encerrada = "encerrada"


def _query_cargas(
    db: Session,
    data_inicial: str,
    data_final: Optional[str] = None,
    status: Optional[StatusCargaFiltro] = None,
):
    # select_cargas.sql busca o valor da carga com uma subconsulta correlacionada
    # em SE1070 (nota fiscal), casando filial/série/número/cliente/loja — não é
    # DAK_VALOR. ISNULL(...,0) na query original == coalesce(...,0) aqui.
    #
    # NOTA: já tentamos trocar esta subconsulta por um LEFT JOIN único (supondo
    # que seria mais rápido para relatórios de vários dias), mas a mudança
    # piorou a performance real no SQL Server — provável indício de que
    # SE1070 tem índice em (E1_FILIAL, E1_PREFIXO, E1_NUM, ...) que permite ao
    # otimizador resolver a subconsulta correlacionada como um INDEX SEEK por
    # linha (rápido), enquanto o LEFT JOIN forçou um plano de hash/merge join
    # varrendo bem mais de SE1070 do que o necessário. Revertido para a forma
    # original; não mexer nisso de novo sem antes conferir o plano de
    # execução real (SSMS "Actual Execution Plan" ou SET STATISTICS IO/TIME)
    # e os índices existentes em SE1070.
    valor_nota_fiscal = (
        select(NotaFiscalSaida.valor)
        .where(
            NotaFiscalSaida.filial == ItemCarga.filial,
            NotaFiscalSaida.cliente == ItemCarga.cliente,
            NotaFiscalSaida.loja == ItemCarga.loja,
            NotaFiscalSaida.prefixo == ItemCarga.serie,
            NotaFiscalSaida.numero == ItemCarga.nota_fiscal,
            NotaFiscalSaida.parcela == '  ',
            NotaFiscalSaida.tipo == 'NF ',
            NotaFiscalSaida.carga == ItemCarga.codigo,
            NotaFiscalSaida.sequencia_carga == ItemCarga.sequencia_carga,
            NotaFiscalSaida.deletado != "*",
        )
        .correlate(ItemCarga)
        .scalar_subquery()
    )
    valor_coluna = func.coalesce(valor_nota_fiscal, 0)

    query = (
        db.query(
            ItemCarga.filial,
            ItemCarga.codigo,
            ItemCarga.data,
            ItemCarga.pedido,
            ItemCarga.cliente,
            ItemCarga.peso,
            ItemCarga.nota_fiscal,
            VeiculoCarga.caminhao,
            VeiculoCarga.status,
            Cliente.nome,
            valor_coluna,
        )
        .join(
            VeiculoCarga,
            and_(
                VeiculoCarga.deletado != "*",
                VeiculoCarga.filial == ItemCarga.filial,
                VeiculoCarga.codigo == ItemCarga.codigo,
                VeiculoCarga.sequencia_carga == ItemCarga.sequencia_carga,
            ),
        )
        .join(
            Cliente,
            and_(
                Cliente.deletado != "*",
                Cliente.filial == ItemCarga.filial,
                Cliente.codigo == ItemCarga.cliente,
                Cliente.loja == ItemCarga.loja,
            ),
        )
        .filter(
            ItemCarga.deletado != "*",
            ItemCarga.sequencia != _SEQUENCIA_CANCELADA,
            # Diferente do select_cargas.sql original (data mínima fixa em
            # '20260801'), aqui a data é parametrizável via query string: cada
            # cliente/integração decide a partir de qual data quer consultar
            # as cargas. Sem o parâmetro, assume a data atual do sistema.
            ItemCarga.data >= data_inicial,
        )
    )
    if data_final:
        query = query.filter(ItemCarga.data <= data_final)
    if status == StatusCargaFiltro.encerrada:
        query = query.filter(VeiculoCarga.status.in_(_STATUS_CARGA_FECHADOS))
    elif status == StatusCargaFiltro.aberta:
        query = query.filter(VeiculoCarga.status.notin_(_STATUS_CARGA_FECHADOS))
    return query


@router.get("/", response_model=PaginatedResponse[CargaRead])
def listar_cargas(
    skip: int = 0,
    limit: int = Query(50, le=200),
    data_inicial: Optional[str] = Query(
        None,
        description="Data mínima da carga, formato AAAAMMDD (DAI_DATA >= data_inicial). "
        "Sem o parâmetro, assume a data atual do sistema.",
    ),
    data_final: Optional[str] = Query(
        None,
        description="Data máxima da carga, formato AAAAMMDD (DAI_DATA <= data_final). "
        "Sem o parâmetro, não há limite superior.",
    ),
    status: Optional[StatusCargaFiltro] = Query(
        None,
        description="Filtra pelo status da carga (DAK_ACECAR), classificado em "
        "apenas 2 tipos: 'encerrada' (códigos 7 ou 8) ou 'aberta' (demais "
        "códigos). Sem o parâmetro, traz cargas de qualquer status.",
    ),
    db: Session = Depends(get_db),
):
    data_filtro = data_inicial or date.today().strftime("%Y%m%d")
    query = _query_cargas(db, data_filtro, data_final, status)
    total = query.count()
    # order_by aplicado apenas aqui (após o count()): o MSSQL exige ORDER BY
    # junto de OFFSET/LIMIT, mas não aceita ORDER BY dentro da subquery que o
    # SQLAlchemy gera para count() quando não há TOP/OFFSET nela.
    linhas = (
        query.order_by(ItemCarga.filial, ItemCarga.codigo, ItemCarga.sequencia_carga)
        .offset(skip)
        .limit(limit)
        .all()
    )

    items = [
        CargaRead(
            filial=filial,
            codigo=codigo,
            data=data,
            pedido=pedido,
            cliente=cliente,
            nome_cliente=nome_cliente,
            peso=peso,
            nota_fiscal=nota_fiscal,
            caminhao=caminhao,
            status_carga=status_carga,
            valor=valor,
        )
        for (
            filial, codigo, data, pedido, cliente, peso, nota_fiscal,
            caminhao, status_carga, nome_cliente, valor,
        ) in linhas
    ]

    return {"total": total, "skip": skip, "limit": limit, "items": items}
