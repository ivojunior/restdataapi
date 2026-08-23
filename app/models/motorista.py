from sqlalchemy import Column, Integer, String

from app.database import Base


class Motorista(Base):
    """Mapeamento somente leitura da tabela DA4070 (Motoristas) do Protheus.

    Tabela gerenciada externamente pelo Protheus: nunca é criada/alterada por este
    projeto (veja a lista TABELAS_EXTERNAS em alembic/env.py). Usada apenas como
    apoio (join opcional) no relatório de cargas, para obter o nome do motorista
    (DAK_MOTORI) do veículo — sem rota própria.
    """

    __tablename__ = "DA4070"

    rec_no = Column("R_E_C_N_O_", Integer, primary_key=True)
    deletado = Column("D_E_L_E_T_", String(1))

    filial = Column("DA4_FILIAL", String(2))
    codigo = Column("DA4_COD", String(6))
    nome = Column("DA4_NOME", String(40))
