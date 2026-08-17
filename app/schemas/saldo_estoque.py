from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SaldoEstoqueRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rec_no: int
    filial: str
    codigo_produto: str
    local: str
    saldo_atual: Decimal
    quantidade_empenhada: Optional[Decimal] = None
    quantidade_reservada: Optional[Decimal] = None
    quantidade_pedido_venda: Optional[Decimal] = None
    quantidade_pedido_compra: Optional[Decimal] = None
    custo_medio: Optional[Decimal] = None
