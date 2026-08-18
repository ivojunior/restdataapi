from sqlalchemy import Column, Integer, String

from app.database import Base


class Cliente(Base):
    """Mapeamento somente leitura da tabela SA1070 (Clientes) do Protheus.

    Tabela gerenciada externamente pelo Protheus: nunca é criada/alterada por este
    projeto (veja a lista TABELAS_EXTERNAS em alembic/env.py). Usada apenas como
    apoio (join) no relatório de cargas, sem rota própria.
    """

    __tablename__ = "SA1070"

    rec_no = Column("R_E_C_N_O_", Integer, primary_key=True)
    deletado = Column("D_E_L_E_T_", String(1))

    filial = Column("A1_FILIAL", String(2))
    codigo = Column("A1_COD", String(6))
    loja = Column("A1_LOJA", String(3))
    nome = Column("A1_NOME", String(40))
