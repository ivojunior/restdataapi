from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class FinanceiroRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    filial: str
    numero: str
    parcela: str
    tipo: str
    codigo_operacao: Optional[str] = None
    descricao_operacao: Optional[str] = None
    valor: Decimal
    saldo: Decimal
    emissao: str
    vencimento_real: str
    nome_fornecedor: Optional[str] = None
    data_baixa: Optional[str] = None
    historico: str
    recuperacao_judicial: Optional[str] = None
