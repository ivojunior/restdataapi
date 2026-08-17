from typing import Optional

from pydantic import BaseModel, ConfigDict


class FornecedorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rec_no: int
    filial: str
    codigo: str
    loja: str
    nome: str
    nome_reduzido: Optional[str] = None
    cnpj_cpf: Optional[str] = None
    inscricao_estadual: Optional[str] = None
    endereco: Optional[str] = None
    bairro: Optional[str] = None
    municipio: Optional[str] = None
    estado: Optional[str] = None
    cep: Optional[str] = None
    ddd: Optional[str] = None
    telefone: Optional[str] = None
    contato: Optional[str] = None
    tipo: Optional[str] = None
    bloqueado: Optional[str] = None
