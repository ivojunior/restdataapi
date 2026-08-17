from sqlalchemy import Column, Integer, String

from app.database import Base


class Fornecedor(Base):
    """Mapeamento somente leitura da tabela SA2070 (Fornecedores) do Protheus.

    Tabela gerenciada externamente pelo Protheus: nunca é criada/alterada por este
    projeto (veja a lista TABELAS_EXTERNAS em alembic/env.py).
    """

    __tablename__ = "SA2070"

    rec_no = Column("R_E_C_N_O_", Integer, primary_key=True)
    deletado = Column("D_E_L_E_T_", String(1))

    filial = Column("A2_FILIAL", String(2))
    codigo = Column("A2_COD", String(6))
    loja = Column("A2_LOJA", String(3))
    nome = Column("A2_NOME", String(40))
    nome_reduzido = Column("A2_NREDUZ", String(20))
    cnpj_cpf = Column("A2_CGC", String(20))
    inscricao_estadual = Column("A2_INSCR", String(20))
    endereco = Column("A2_END", String(60))
    bairro = Column("A2_BAIRRO", String(30))
    municipio = Column("A2_MUN", String(20))
    estado = Column("A2_EST", String(2))
    cep = Column("A2_CEP", String(9))
    ddd = Column("A2_DDD", String(3))
    telefone = Column("A2_TEL", String(15))
    contato = Column("A2_CONTATO", String(30))
    tipo = Column("A2_TIPO", String(1))
    bloqueado = Column("A2_MSBLQL", String(1))
