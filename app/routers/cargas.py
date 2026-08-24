import enum
from datetime import date
from typing import Optional

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.models.cliente import Cliente
from app.models.item_carga import ItemCarga
from app.models.motorista import Motorista
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
# "fechados" por select_cargas.sql (CASE ... ELSE 'Aberta'). Qualquer código
# fora dessa lista — incluindo NULL — é "aberto".
#
# NOTA histórica: select_cargas.sql já alternou entre este ELSE catch-all e
# uma enumeração explícita de códigos "abertos" (sem ELSE, deixando um
# código desconhecido como NULL). Se voltar a mudar, o ponto de ajuste é
# só aqui + o filtro "aberta" abaixo (que precisa tratar NULL do mesmo jeito
# que o CASE de status_coluna trata).
_STATUS_CARGA_FECHADOS = ("7", "8")

# Placa usada para indicar que o próprio cliente retirou a carga (sem
# caminhão terceirizado vinculado) — select_cargas.sql substitui por
# "Cliente" via CASE; réplica aqui (era feito no client desktop antes).
_CAMINHAO_CLIENTE = "KHA0902"


class StatusCargaFiltro(str, enum.Enum):
    """Classificação do status da carga (DAK_ACECAR) em apenas 2 tipos:
    "encerrada" (códigos 7 e 8) ou "aberta" (demais códigos, incluindo NULL).

    O nome do parâmetro de query ("encerrada") é mantido por
    retrocompatibilidade; o texto de fato retornado no campo status_carga
    (ver case() em _query_cargas) é "Fechada".
    """

    aberta = "aberta"
    encerrada = "encerrada"


# NOTA histórica: já tentamos paginar em duas fases — uma consulta rasa só
# com R_E_C_N_O_ (chave primária de DAI070) para achar a página, seguida de
# uma segunda consulta com WHERE R_E_C_N_O_ IN (<até `limit` valores>) para
# buscar a projeção completa (joins de apoio + subquery de valor) só para
# essas linhas. Na teoria isso evitaria que o banco calculasse a subquery/
# joins de apoio para mais linhas do que a página. Na prática, medido contra
# o SQL Server real, foi MUITO mais lento que a query única abaixo — provável
# indício de que R_E_C_N_O_ não tem índice de suporte nesta instalação do
# Protheus (é um identificador interno, não necessariamente indexado como
# chave de busca), forçando um scan para resolver o IN(...) da segunda
# consulta, além do custo de reabrir todos os joins do zero. Revertido para
# a query única; não tentar essa estratégia de novo sem antes confirmar
# (via sys.indexes ou o Execution Plan) que R_E_C_N_O_ tem um índice único
# em DAI070.
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
    # Diferente da consulta original, também restringimos parcela ('  ') e tipo
    # ('NF ') e casamos por carga/sequência de carga (E1_YCARGA/E1_YSEQCAR,
    # campos customizados desta instalação do Protheus) — evita que a
    # subconsulta pegue, por engano, uma nota de outra parcela/tipo ou de outra
    # carga que coincida em filial/série/número/cliente/loja, dando mais
    # assertividade ao valor retornado.
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

    # select_cargas.sql agora calcula CAMINHAO e STATUS com CASE direto no
    # banco (em vez de devolver os códigos brutos e formatar no client) —
    # replicado aqui com case() do SQLAlchemy. Isso não afeta o plano de
    # execução (não entra em JOIN/WHERE, só na lista de colunas do SELECT) e
    # tira do client o trabalho de formatar essas duas colunas linha a linha.
    caminhao_coluna = case(
        (VeiculoCarga.caminhao == _CAMINHAO_CLIENTE, "Cliente"),
        else_=VeiculoCarga.caminhao,
    )
    status_coluna = case(
        (VeiculoCarga.status.in_(_STATUS_CARGA_FECHADOS), "Fechada"),
        else_="Aberta",
    )

    query = (
        db.query(
            ItemCarga.filial,
            ItemCarga.codigo,
            ItemCarga.data,
            ItemCarga.pedido,
            Motorista.nome,
            ItemCarga.cliente,
            ItemCarga.peso,
            ItemCarga.nota_fiscal,
            caminhao_coluna,
            status_coluna,
            Cliente.nome,
            Cliente.bairro,
            Cliente.municipio,
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
        # DA4070 (motorista) é LEFT JOIN em select_cargas.sql — veículo sem
        # motorista cadastrado continua aparecendo, só com motorista nulo.
        # DA5070 (percurso) saiu da consulta nesta versão de select_cargas.sql
        # (nem o join nem a descrição são mais usados).
        .outerjoin(
            Motorista,
            and_(
                Motorista.deletado != "*",
                Motorista.filial == VeiculoCarga.filial,
                Motorista.codigo == VeiculoCarga.motorista,
            ),
        )
        .filter(
            ItemCarga.deletado != "*",
            ItemCarga.sequencia != _SEQUENCIA_CANCELADA,
            # Diferente do select_cargas.sql original (data mínima fixa em
            # '20260801'), aqui a data é parametrizável via query string: cada
            # cliente/integração decide a partir de qual data quer consultar
            # as cargas. Sem o parâmetro, assume a data atual do sistema.
            #
            # Filtra por VeiculoCarga.data (DAK_DATA), não ItemCarga.data
            # (DAI_DATA): DAK070 tem uma linha por veículo/sequência de carga,
            # bem menos linhas que DAI070 (uma por item) — filtrar na tabela
            # menor é mais barato. O campo `data` retornado em CargaRead
            # continua vindo de DAI070 (data do item), sem mudança — só o
            # predicado do filtro migrou de tabela.
            VeiculoCarga.data >= data_inicial,
        )
    )
    if data_final:
        query = query.filter(VeiculoCarga.data <= data_final)
    if status == StatusCargaFiltro.encerrada:
        query = query.filter(VeiculoCarga.status.in_(_STATUS_CARGA_FECHADOS))
    elif status == StatusCargaFiltro.aberta:
        # VeiculoCarga.status.notin_(...) sozinho tem o problema clássico do
        # NOT IN com NULL em SQL: se DAK_ACECAR for NULL, "NULL NOT IN (...)"
        # nunca é verdadeiro (lógica de três valores) — a carga sumiria do
        # filtro "aberta" mesmo o case() de status_coluna (com ELSE) já
        # classificando NULL como "Aberta". or_(is_(None), ...) replica
        # explicitamente essa mesma regra do ELSE no filtro.
        query = query.filter(
            or_(
                VeiculoCarga.status.is_(None),
                VeiculoCarga.status.notin_(_STATUS_CARGA_FECHADOS),
            )
        )
    return query


@router.get("/", response_model=PaginatedResponse[CargaRead])
def listar_cargas(
    skip: int = 0,
    limit: int = Query(50, le=200),
    data_inicial: Optional[str] = Query(
        None,
        description="Data mínima da carga, formato AAAAMMDD (DAK_DATA >= data_inicial). "
        "Sem o parâmetro, assume a data atual do sistema.",
    ),
    data_final: Optional[str] = Query(
        None,
        description="Data máxima da carga, formato AAAAMMDD (DAK_DATA <= data_final). "
        "Sem o parâmetro, não há limite superior.",
    ),
    status: Optional[StatusCargaFiltro] = Query(
        None,
        description="Filtra pelo status da carga (DAK_ACECAR), classificado em "
        "apenas 2 tipos: 'encerrada' (códigos 7 ou 8) ou 'aberta' (demais "
        "códigos, incluindo nulo). Sem o parâmetro, traz cargas de qualquer status.",
    ),
    db: Session = Depends(get_db),
):
    data_filtro = data_inicial or date.today().strftime("%Y%m%d")
    query = _query_cargas(db, data_filtro, data_final, status)
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
            motorista=motorista,
            cliente=cliente,
            nome_cliente=nome_cliente,
            bairro_cliente=bairro_cliente,
            municipio_cliente=municipio_cliente,
            peso=peso,
            nota_fiscal=nota_fiscal,
            caminhao=caminhao,
            status_carga=status_carga,
            valor=valor,
        )
        for (
            filial, codigo, data, pedido, motorista, cliente, peso, nota_fiscal,
            caminhao, status_carga, nome_cliente, bairro_cliente, municipio_cliente,
            valor,
        ) in linhas
    ]

    return {"skip": skip, "limit": limit, "items": items}
