from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SaldoEstoqueRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    filial: str
    local: str
    codigo_produto: str
    descricao_produto: Optional[str] = None
    quantidade: Decimal
    valor_atual: Optional[Decimal] = None
