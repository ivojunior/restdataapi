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


class StatusCarga(str, enum.Enum):
    """Valores de DAK_ACECAR confirmados pelo usuário para esta customização
    (o campo não tem lista pública de opções — veja app/models/veiculo_carga.py)."""

    montada = "1"
    disp_conf_gega = "2"
    disp_prest_contas = "3"
    disp_prest_titulos = "6"
    encerrada = "7"
    juros_pendentes = "8"


def _query_cargas(
    db: Session,
    data_inicial: str,
    data_final: Optional[str] = None,
    status: Optional[StatusCarga] = None,
):
    # select_cargas.sql busca o valor da carga com uma subconsulta correlacionada
    # em SE1070 (nota fiscal), casando filial/série/número/cliente/loja — não é
    # DAK_VALOR. ISNULL(...,0) na query original == coalesce(...,0) aqui.
    valor_nota_fiscal = (
        select(NotaFiscalSaida.valor)
        .where(
            NotaFiscalSaida.deletado != "*",
            NotaFiscalSaida.filial == ItemCarga.filial,
            NotaFiscalSaida.prefixo == ItemCarga.serie,
            NotaFiscalSaida.numero == ItemCarga.nota_fiscal,
            NotaFiscalSaida.cliente == ItemCarga.cliente,
            NotaFiscalSaida.loja == ItemCarga.loja,
        )
        .correlate(ItemCarga)
        .scalar_subquery()
    )
    valor_coluna = func.coalesce(valor_nota_fiscal, 0)

    query = (
        db.query(ItemCarga, VeiculoCarga, Cliente.nome, valor_coluna)
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
    if status:
        query = query.filter(VeiculoCarga.status == status.value)
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
    status: Optional[StatusCarga] = Query(
        None,
        description="Filtra pelo status da carga (DAK_ACECAR): 1=Montada, "
        "2=Disp Conf Gega, 3=Disp Prest Contas, 6=Disp Prest Títulos, "
        "7=Encerrada, 8=Juros Pendentes. Sem o parâmetro, traz cargas de "
        "qualquer status.",
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
            filial=item.filial,
            codigo=item.codigo,
            data=item.data,
            pedido=item.pedido,
            cliente=item.cliente,
            nome_cliente=nome_cliente,
            peso=item.peso,
            nota_fiscal=item.nota_fiscal,
            caminhao=veiculo.caminhao,
            status_carga=veiculo.status,
            valor=valor,
        )
        for item, veiculo, nome_cliente, valor in linhas
    ]

    return {"total": total, "skip": skip, "limit": limit, "items": items}
