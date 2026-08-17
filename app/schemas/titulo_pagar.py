from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TituloPagarRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rec_no: int
    filial: str
    prefixo: str
    numero: str
    parcela: str
    tipo: str
    fornecedor: str
    loja: str
    emissao: str
    vencimento_original: str
    vencimento: str
    valor: Decimal
    saldo: Decimal
    moeda: str
    historico: str
    data_baixa: Optional[str] = None
