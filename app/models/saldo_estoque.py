from sqlalchemy import Column, Integer, Numeric, String

from app.database import Base


class SaldoEstoque(Base):
    """Mapeamento somente leitura da tabela SB2070 (Saldos de Estoque) do Protheus.

    Tabela gerenciada externamente pelo Protheus: nunca é criada/alterada por este
    projeto (veja a lista TABELAS_EXTERNAS em alembic/env.py).
    """

    __tablename__ = "SB2070"

    rec_no = Column("R_E_C_N_O_", Integer, primary_key=True)
    deletado = Column("D_E_L_E_T_", String(1))

    filial = Column("B2_FILIAL", String(2))
    codigo_produto = Column("B2_COD", String(15))
    local = Column("B2_LOCAL", String(2))
    saldo_atual = Column("B2_QATU", Numeric(18, 4))
    quantidade_empenhada = Column("B2_QEMP", Numeric(18, 4))
    quantidade_reservada = Column("B2_RESERVA", Numeric(18, 4))
    quantidade_pedido_venda = Column("B2_QPEDVEN", Numeric(18, 4))
    quantidade_pedido_compra = Column("B2_QPEDCOM", Numeric(18, 4))
    custo_medio = Column("B2_CM1", Numeric(18, 4))
