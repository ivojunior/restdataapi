from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ProdutoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rec_no: int
    filial: str
    codigo: str
    descricao: str
    tipo: Optional[str] = None
    unidade_medida: Optional[str] = None
    grupo: Optional[str] = None
    local_padrao: Optional[str] = None
    ncm: Optional[str] = None
    peso_liquido: Optional[Decimal] = None
    peso_bruto: Optional[Decimal] = None
    codigo_barras: Optional[str] = None
    preco_venda: Optional[Decimal] = None
    bloqueado: Optional[str] = None
