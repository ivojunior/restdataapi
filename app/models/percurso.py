from sqlalchemy import Column, Integer, String

from app.database import Base


class Percurso(Base):
    """Mapeamento somente leitura da tabela DA5070 (Percursos) do Protheus.

    Tabela gerenciada externamente pelo Protheus: nunca é criada/alterada por este
    projeto (veja a lista TABELAS_EXTERNAS em alembic/env.py). Usada apenas como
    apoio (join) no relatório de cargas, para obter a descrição do percurso
    (DAI_PERCUR) do item de carga — sem rota própria.
    """

    __tablename__ = "DA5070"

    rec_no = Column("R_E_C_N_O_", Integer, primary_key=True)
    deletado = Column("D_E_L_E_T_", String(1))

    filial = Column("DA5_FILIAL", String(2))
    codigo = Column("DA5_COD", String(6))
    descricao = Column("DA5_DESC", String(40))
