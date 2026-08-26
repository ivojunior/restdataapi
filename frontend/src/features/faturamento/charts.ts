import type { PontoGrafico } from '../../components/charts/types'
import type { FaturamentoItem } from './types'

function somarPor(
  itens: FaturamentoItem[],
  chave: (item: FaturamentoItem) => string | number,
  campo: 'faturamento' | 'lucro_bruto',
): Map<string | number, number> {
  const mapa = new Map<string | number, number>()
  for (const item of itens) {
    const k = chave(item)
    mapa.set(k, (mapa.get(k) ?? 0) + Number(item[campo]))
  }
  return mapa
}

function topN(mapa: Map<string | number, number>, n: number): PontoGrafico[] {
  return [...mapa.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, n)
    .map(([rotulo, valor]) => ({ rotulo, valor }))
}

const rotuloProduto = (item: FaturamentoItem) => `${item.codigo} — ${(item.descricao ?? '').slice(0, 24)}`

export function topProdutosPorFaturamento(itens: FaturamentoItem[], n = 10): PontoGrafico[] {
  return topN(somarPor(itens, rotuloProduto, 'faturamento'), n)
}

export function topProdutosPorLucro(itens: FaturamentoItem[], n = 10): PontoGrafico[] {
  return topN(somarPor(itens, rotuloProduto, 'lucro_bruto'), n)
}

export function faturamentoPorFilial(itens: FaturamentoItem[]): PontoGrafico[] {
  const mapa = somarPor(itens, (i) => i.filial, 'faturamento')
  return [...mapa.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([rotulo, valor]) => ({ rotulo, valor }))
}

export function faturamentoPorDia(itens: FaturamentoItem[]): PontoGrafico[] {
  const mapa = new Map<number, number>()
  for (const item of itens) {
    mapa.set(item.dia, (mapa.get(item.dia) ?? 0) + Number(item.faturamento))
  }
  return [...mapa.entries()]
    .sort((a, b) => a[0] - b[0])
    .map(([rotulo, valor]) => ({ rotulo, valor }))
}
