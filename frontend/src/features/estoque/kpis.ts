import { paraNumero } from '../../utils/format'
import type { EstoqueItem } from './types'

export interface KpisEstoque {
  totalItens: number
  filiais: number
  quantidadeTotal: number
  valorTotal: number
  valorMedio: number
}

/** Réplica de `_update_kpis` em client/app_estoque.py. */
export function calcularKpis(itens: EstoqueItem[]): KpisEstoque {
  const valorTotal = itens.reduce((soma, i) => soma + (paraNumero(i.valor_atual) || 0), 0)
  const quantidadeTotal = itens.reduce((soma, i) => soma + Number(i.quantidade), 0)

  return {
    totalItens: itens.length,
    filiais: new Set(itens.map((i) => i.filial)).size,
    quantidadeTotal,
    valorTotal,
    valorMedio: quantidadeTotal ? valorTotal / quantidadeTotal : 0,
  }
}
