import type { FaturamentoItem } from './types'

export interface KpisFaturamento {
  registros: number
  produtos: number
  quantidadeTotal: number
  faturamentoTotal: number
  custoTotal: number
  precoMedioAcumulado: number
  lucroBrutoTotal: number
  margemGeral: number
  markupGeral: number
}

/** Réplica de `_update_kpis` em client/app_faturamento.py. */
export function calcularKpis(itens: FaturamentoItem[]): KpisFaturamento {
  const faturamentoTotal = itens.reduce((soma, i) => soma + Number(i.faturamento), 0)
  const custoTotal = itens.reduce((soma, i) => soma + Number(i.custo), 0)
  const quantidadeTotal = itens.reduce((soma, i) => soma + Number(i.quantidade), 0)
  const lucroBrutoTotal = itens.reduce((soma, i) => soma + Number(i.lucro_bruto), 0)

  return {
    registros: itens.length,
    produtos: new Set(itens.map((i) => i.codigo)).size,
    quantidadeTotal,
    faturamentoTotal,
    custoTotal,
    // Ponderado pelos totais, não a média da coluna preco_medio — mesma
    // lógica de "margem geral"/"markup geral" já usada no client desktop
    // (dá peso igual a cada nota, não a cada grupo pequeno ou grande).
    precoMedioAcumulado: quantidadeTotal ? faturamentoTotal / quantidadeTotal : 0,
    lucroBrutoTotal,
    margemGeral: faturamentoTotal ? (lucroBrutoTotal / faturamentoTotal) * 100 : 0,
    markupGeral: custoTotal ? (lucroBrutoTotal / custoTotal) * 100 : 0,
  }
}
