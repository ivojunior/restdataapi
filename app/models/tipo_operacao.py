from sqlalchemy import Column, Integer, String

from app.database import Base


class TipoOperacao(Base):
    """Mapeamento somente leitura da tabela PA6000 (Tipos de Operação Financeira) do Protheus.

    Tabela gerenciada externamente pelo Protheus: nunca é criada/alterada por este
    projeto (veja a lista TABELAS_EXTERNAS em alembic/env.py). Usada apenas para
    enriquecer o relatório financeiro com a descrição do tipo de operação (E2_YOPER).
    """

    __tablename__ = "PA6000"

    rec_no = Column("R_E_C_N_O_", Integer, primary_key=True)
    deletado = Column("D_E_L_E_T_", String(1))

    filial = Column("PA6_FILIAL", String(2))
    codigo = Column("PA6_COD", String(6))
    descricao = Column("PA6_DESCR", String(40))
