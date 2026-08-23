from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CargaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    filial: str
    codigo: str
    data: str
    # Só a descrição do percurso é exposta (select_cargas.sql não seleciona
    # mais DAI_PERCUR, só DA5_DESC); join com DA5070 é opcional (LEFT JOIN),
    # então vem None quando o item não tem percurso cadastrado.
    descricao_percurso: Optional[str] = None
    pedido: str
    # Nome do motorista (DA4_NOME, join opcional com DA4070 via DAK_MOTORI);
    # None quando o veículo não tem motorista cadastrado.
    motorista: Optional[str] = None
    cliente: str
    nome_cliente: Optional[str] = None
    peso: Decimal
    nota_fiscal: str
    # Já vêm formatados pela API (case do SQL/SQLAlchemy — ver
    # app/routers/cargas.py): "Cliente" no lugar da placa KHA0902.
    caminhao: str
    # O CASE de status_carga não tem ELSE (só classifica DAK_ACECAR em
    # ('1'..'6') como "Aberta" e ('7','8') como "Fechada") — qualquer outro
    # código, ou NULL, resulta em status_carga None.
    status_carga: Optional[str] = None
    valor: Decimal
