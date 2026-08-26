from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class FaturamentoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    filial: str
    # Dia do mês da emissão (1-31) — não é uma data completa. Réplica de
    # DAY(D2_EMISSAO) em select_faturamento.sql: se o período (data_inicial/
    # data_final) atravessar mais de um mês, dias iguais de meses diferentes
    # são somados juntos no mesmo grupo (ex.: dia 5 de janeiro e dia 5 de
    # fevereiro viram um único "dia 5"). Ver app/routers/faturamento.py.
    dia: int
    codigo: str
    descricao: str
    quantidade: Decimal
    # None quando o denominador da razão é zero para este grupo (ex.: só
    # bonificação, sem venda, no mesmo filial/dia/produto — faturamento
    # zero) — ver o comentário sobre func.nullif em _query_faturamento.
    # "Não é possível calcular", não "zero".
    preco_medio: Optional[Decimal]
    faturamento: Decimal
    custo: Decimal
    lucro_bruto: Decimal
    margem: Optional[Decimal]
    markup: Optional[Decimal]
