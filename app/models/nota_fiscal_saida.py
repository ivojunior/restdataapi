from sqlalchemy import Column, Integer, Numeric, String

from app.database import Base


class NotaFiscalSaida(Base):
    """Mapeamento somente leitura da tabela SE1070 (Notas Fiscais de Saída) do Protheus.

    Tabela gerenciada externamente pelo Protheus: nunca é criada/alterada por este
    projeto (veja a lista TABELAS_EXTERNAS em alembic/env.py). Usada apenas como
    apoio (subconsulta correlacionada) no relatório de cargas, para obter o valor
    da nota fiscal vinculada ao item de carga (réplica de select_cargas.sql) — sem
    rota própria.
    """

    __tablename__ = "SE1070"

    rec_no = Column("R_E_C_N_O_", Integer, primary_key=True)
    deletado = Column("D_E_L_E_T_", String(1))

    filial = Column("E1_FILIAL", String(2))
    prefixo = Column("E1_PREFIXO", String(3))
    tipo = Column("E1_TIPO", String(3))
    parcela = Column("E1_PARCELA", String(2))
    numero = Column("E1_NUM", String(9))
    cliente = Column("E1_CLIENTE", String(6))
    loja = Column("E1_LOJA", String(2))
    valor = Column("E1_VALOR", Numeric(18, 2))
    carga = Column("E1_YCARGA", String(6))
    sequencia_carga = Column("E1_YSEQCAR", String(2))

