from sqlalchemy import Column, Integer, Numeric, String

from app.database import Base


class Produto(Base):
    """Mapeamento somente leitura da tabela SB1000 (Cadastro de Produtos) do Protheus.

    Tabela gerenciada externamente pelo Protheus: nunca é criada/alterada por este
    projeto (veja a lista TABELAS_EXTERNAS em alembic/env.py).
    """

    __tablename__ = "SB1000"

    rec_no = Column("R_E_C_N_O_", Integer, primary_key=True)
    deletado = Column("D_E_L_E_T_", String(1))

    filial = Column("B1_FILIAL", String(2))
    codigo = Column("B1_COD", String(15))
    descricao = Column("B1_DESC", String(60))
    tipo = Column("B1_TIPO", String(2))
    unidade_medida = Column("B1_UM", String(2))
    grupo = Column("B1_GRUPO", String(4))
    local_padrao = Column("B1_LOCPAD", String(2))
    conversao = Column("B1_CONV", Numeric(18, 4))
    ncm = Column("B1_POSIPI", String(10))
    peso_liquido = Column("B1_PESO", Numeric(18, 4))
    peso_bruto = Column("B1_PESBRUTO", Numeric(18, 4))
    codigo_barras = Column("B1_CODBAR", String(20))
    preco_venda = Column("B1_PRV1", Numeric(18, 2))
    bloqueado = Column("B1_MSBLQL", String(1))
