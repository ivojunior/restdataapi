from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CargaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    filial: str
    codigo: str
    data: str
    percurso: str
    descricao_percurso: Optional[str] = None
    pedido: str
    cliente: str
    nome_cliente: Optional[str] = None
    peso: Decimal
    nota_fiscal: str
    # Já vêm formatados pela API (case do SQL/SQLAlchemy — ver
    # app/routers/cargas.py): "Cliente" no lugar da placa KHA0902, e
    # "Aberta"/"Fechada" no lugar do código bruto de DAK_ACECAR.
    caminhao: str
    status_carga: str
    valor: Decimal
