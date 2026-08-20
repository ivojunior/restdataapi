from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CargaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    filial: str
    codigo: str
    data: str
    pedido: str
    cliente: str
    nome_cliente: Optional[str] = None
    peso: Decimal
    nota_fiscal: str
    caminhao: str
    status_carga: Optional[str] = None
    valor: Decimal
