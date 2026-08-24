from sqlalchemy import Column, Integer, String

from app.database import Base


class VeiculoCarga(Base):
    """Mapeamento somente leitura da tabela DAK070 (Veículos da Carga) do Protheus.

    Tabela gerenciada externamente pelo Protheus: nunca é criada/alterada por este
    projeto (veja a lista TABELAS_EXTERNAS em alembic/env.py). Usada apenas como
    apoio (join) no relatório de cargas, sem rota própria.
    """

    __tablename__ = "DAK070"

    rec_no = Column("R_E_C_N_O_", Integer, primary_key=True)
    deletado = Column("D_E_L_E_T_", String(1))

    filial = Column("DAK_FILIAL", String(2))
    codigo = Column("DAK_COD", String(6))
    sequencia_carga = Column("DAK_SEQCAR", String(2))
    # Formato AAAAMMDD (string), igual a DAI_DATA em DAI070 — usado para
    # filtrar data_inicial/data_final no relatório de cargas (ver
    # app/routers/cargas.py): DAK070 tem uma linha por veículo/sequência de
    # carga, bem menos linhas que DAI070 (uma por item), então filtrar aqui
    # é mais barato do que filtrar em DAI070.
    data = Column("DAK_DATA", String(8))
    caminhao = Column("DAK_CAMINH", String(10))
    motorista = Column("DAK_MOTORI", String(6))
    # Apesar do nome (dicionário padrão do Protheus: "Acerto de Carga Ok?"),
    # nesta instalação DAK_ACECAR foi customizado para guardar o status da
    # carga ("1"=Montada, "2"=Disp Conf Gega, "3"=Disp Prest Contas,
    # "6"=Disp Prest Títulos, "7"=Encerrada, "8"=Juros Pendentes —
    # confirmado pelo usuário; não há lista pública desses valores para
    # esse campo, que é específico desta customização).
    status = Column("DAK_ACECAR", String(1))
