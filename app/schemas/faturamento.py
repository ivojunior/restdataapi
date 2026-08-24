from decimal import Decimal

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
    faturamento: Decimal
    preco_medio: Decimal
    lucro_bruto: Decimal
    margem: Decimal
