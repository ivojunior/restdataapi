from sqlalchemy import Column, Integer, Numeric, String

from app.database import Base


class TituloPagar(Base):
    """Mapeamento somente leitura da tabela SE2070 (Contas a Pagar) do Protheus.

    Tabela gerenciada externamente pelo Protheus: nunca é criada/alterada por este
    projeto (veja a lista TABELAS_EXTERNAS em alembic/env.py). Datas (E2_EMISSAO,
    E2_VENCTO, E2_VENCORI, E2_VENCREA, E2_BAIXA) são strings "AAAAMMDD", conforme o
    padrão do dicionário de dados do Protheus, e não colunas DATE reais.
    """

    __tablename__ = "SE2070"

    rec_no = Column("R_E_C_N_O_", Integer, primary_key=True)
    deletado = Column("D_E_L_E_T_", String(1))

    filial = Column("E2_FILIAL", String(2))
    prefixo = Column("E2_PREFIXO", String(4))
    numero = Column("E2_NUM", String(9))
    parcela = Column("E2_PARCELA", String(3))
    tipo = Column("E2_TIPO", String(3))
    fornecedor = Column("E2_FORNECE", String(6))
    loja = Column("E2_LOJA", String(3))
    emissao = Column("E2_EMISSAO", String(8))
    vencimento_original = Column("E2_VENCORI", String(8))
    vencimento = Column("E2_VENCTO", String(8))
    vencimento_real = Column("E2_VENCREA", String(8))
    valor = Column("E2_VALOR", Numeric(18, 2))
    saldo = Column("E2_SALDO", Numeric(18, 2))
    moeda = Column("E2_MOEDA", String(2))
    historico = Column("E2_HIST", String(40))
    data_baixa = Column("E2_BAIXA", String(8))
    codigo_operacao = Column("E2_YOPER", String(6))
    nome_fornecedor = Column("E2_NOMFOR", String(40))
    # "1" = título de recuperação judicial; "2" ou vazio = não é.
    recuperacao_judicial = Column("E2_YRJ", String(1))
