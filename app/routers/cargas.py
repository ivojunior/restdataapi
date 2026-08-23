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
from app.models.percurso import Percurso
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
    (ver case() em _projecao_cargas) é "Fechada".
    """

    aberta = "aberta"
    encerrada = "encerrada"


_ORDEM_CARGAS = (ItemCarga.filial, ItemCarga.codigo, ItemCarga.sequencia_carga)


def _filtro_cargas(
    db: Session,
    data_inicial: str,
    data_final: Optional[str] = None,
    status: Optional[StatusCargaFiltro] = None,
):
    """JOINs/filtros que determinam QUAIS itens de carga existem e em que
    ordem — só DAK070 (join obrigatório, também usado no filtro de status)
    e SA1070 (join obrigatório). Não inclui DA5070/DA4070 (LEFT JOIN, nunca
    removem linha) nem a subquery de valor: nenhum dos dois afeta
    quantidade ou ordem das linhas, só os dados extras de cada uma. Usado
    para paginar (fase 1, barata) antes de buscar a projeção completa só
    para a página resultante (fase 2) — ver listar_cargas.
    """
    query = (
        db.query(ItemCarga.rec_no)
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


def _projecao_cargas(db: Session, rec_nos: list):
    """Projeção completa (colunas + joins de apoio + subquery de valor), só
    para os rec_no já escolhidos pela paginação em _filtro_cargas — ver
    comentário em listar_cargas sobre por que separar as duas fases.
    """
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

    return (
        db.query(
            ItemCarga.filial,
            ItemCarga.codigo,
            ItemCarga.data,
            Percurso.descricao,
            ItemCarga.pedido,
            Motorista.nome,
            ItemCarga.cliente,
            ItemCarga.peso,
            ItemCarga.nota_fiscal,
            caminhao_coluna,
            status_coluna,
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
        .outerjoin(
            Percurso,
            and_(
                Percurso.deletado != "*",
                Percurso.filial == ItemCarga.filial,
                Percurso.codigo == ItemCarga.percurso,
            ),
        )
        .outerjoin(
            Motorista,
            and_(
                Motorista.deletado != "*",
                Motorista.filial == VeiculoCarga.filial,
                Motorista.codigo == VeiculoCarga.motorista,
            ),
        )
        # rec_no é a chave primária de DAI070 (R_E_C_N_O_) — filtrar por um
        # IN de no máximo `limit` valores já conhecidos é uma busca por
        # chave, bem mais barata do que reaplicar filtro de data/status
        # sobre a tabela inteira de novo.
        .filter(ItemCarga.rec_no.in_(rec_nos))
    )


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
        "códigos, incluindo nulo). Sem o parâmetro, traz cargas de qualquer status.",
    ),
    db: Session = Depends(get_db),
):
    data_filtro = data_inicial or date.today().strftime("%Y%m%d")

    # Paginação em duas fases: a fase 1 só resolve QUAIS rec_no entram na
    # página (sem os LEFT JOIN de percurso/motorista nem a subquery
    # correlacionada de valor — nenhum dos dois muda quantidade/ordem de
    # linhas). A fase 2 busca a projeção completa filtrando só por esses
    # rec_no (chave primária). Numa única query só (como era antes), o
    # SQL Server pode não conseguir empurrar o OFFSET/FETCH para antes de
    # calcular a subquery/joins de apoio — dependendo do plano escolhido,
    # ele acaba rodando isso para TODAS as linhas que casam no período
    # (que podem ser muito mais que `limit`), não só as da página. Separar
    # em duas fases garante que o trabalho caro só rode para as linhas
    # realmente devolvidas, independente do plano do otimizador.
    rec_nos = [
        rec_no
        for (rec_no,) in (
            _filtro_cargas(db, data_filtro, data_final, status)
            .order_by(*_ORDEM_CARGAS)
            .offset(skip)
            .limit(limit)
            .all()
        )
    ]
    if not rec_nos:
        return {"skip": skip, "limit": limit, "items": []}

    linhas = _projecao_cargas(db, rec_nos).order_by(*_ORDEM_CARGAS).all()

    items = [
        CargaRead(
            filial=filial,
            codigo=codigo,
            data=data,
            descricao_percurso=descricao_percurso,
            pedido=pedido,
            motorista=motorista,
            cliente=cliente,
            nome_cliente=nome_cliente,
            peso=peso,
            nota_fiscal=nota_fiscal,
            caminhao=caminhao,
            status_carga=status_carga,
            valor=valor,
        )
        for (
            filial, codigo, data, descricao_percurso, pedido, motorista, cliente,
            peso, nota_fiscal, caminhao, status_carga, nome_cliente, valor,
        ) in linhas
    ]

    return {"skip": skip, "limit": limit, "items": items}
