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
    # valor = E2_VALOR puro (sem somar retenções). valor_bruto = valor +
    # ISS/INSS/IRRF/CSLL/PIS/COFINS (calculado em app/routers/financeiro.py,
    # réplica de VALOR_BRUTO em select_financeiro.sql) — é o total usado em
    # KPIs/resumos/gráficos, tanto aqui quanto no client desktop e na SPA.
    # Não existe como atributo em TituloPagar (só as parcelas
    # iss/inss/irrf/csll/pis/cofins), daí o default abaixo:
    # model_validate(titulo) preenche com 0 e _montar_items sobrescreve com
    # o valor calculado logo em seguida — igual ao padrão já usado por
    # descricao_operacao (join separado).
    valor: Decimal
    valor_bruto: Decimal = Decimal("0")
    saldo: Decimal
    emissao: str
    vencimento_real: str
    nome_fornecedor: Optional[str] = None
    data_baixa: Optional[str] = None
    historico: str
    recuperacao_judicial: Optional[str] = None
