from sqlalchemy import Column, Integer, Numeric, String

from app.database import Base


class ItemFaturamento(Base):
    """Mapeamento somente leitura da tabela SD2070 (Notas Fiscais de Saída —
    Itens) do Protheus.

    Tabela gerenciada externamente pelo Protheus: nunca é criada/alterada por este
    projeto (veja a lista TABELAS_EXTERNAS em alembic/env.py). Usada como tabela
    principal do relatório de faturamento (junto de SB1000). Não confundir com
    NotaFiscalSaida (SE1070) — tabela diferente, usada só no relatório de cargas.

    `emissao` (D2_EMISSAO) é string "AAAAMMDD", como as demais datas do Protheus
    expostas por esta API — não é uma coluna DATE real.
    """

    __tablename__ = "SD2070"

    rec_no = Column("R_E_C_N_O_", Integer, primary_key=True)
    deletado = Column("D_E_L_E_T_", String(1))

    filial = Column("D2_FILIAL", String(2))
    emissao = Column("D2_EMISSAO", String(8))
    codigo_produto = Column("D2_COD", String(15))
    # Customização desta instalação do Protheus (mesmo padrão de nomenclatura
    # de E2_YOPER em TituloPagar) — código do tipo de operação da nota fiscal.
    # '501' = venda; '542'/'543'/'544' = bonificação (confirmados pelo usuário
    # via select_faturamento.sql — veja app/routers/faturamento.py).
    operacao = Column("D2_YOPER", String(6))
    quantidade = Column("D2_QUANT", Numeric(18, 4))
    total = Column("D2_TOTAL", Numeric(18, 2))
    custo = Column("D2_CUSTO1", Numeric(18, 2))
