from sqlalchemy import Column, Integer, Numeric, String

from app.database import Base


class ItemCarga(Base):
    """Mapeamento somente leitura da tabela DAI070 (Itens de Carga) do Protheus.

    Tabela gerenciada externamente pelo Protheus: nunca é criada/alterada por este
    projeto (veja a lista TABELAS_EXTERNAS em alembic/env.py). Usada como tabela
    principal do relatório de cargas (junto de DAK070 e SA1070).
    """

    __tablename__ = "DAI070"

    rec_no = Column("R_E_C_N_O_", Integer, primary_key=True)
    deletado = Column("D_E_L_E_T_", String(1))

    filial = Column("DAI_FILIAL", String(2))
    codigo = Column("DAI_COD", String(6))
    sequencia_carga = Column("DAI_SEQCAR", String(2))
    sequencia = Column("DAI_SEQUEN", String(6))
    data = Column("DAI_DATA", String(8))
    pedido = Column("DAI_PEDIDO", String(6))
    cliente = Column("DAI_CLIENT", String(6))
    loja = Column("DAI_LOJA", String(3))
    peso = Column("DAI_PESO", Numeric(18, 4))
    nota_fiscal = Column("DAI_NFISCA", String(9))
    serie = Column("DAI_SERIE", String(3))
