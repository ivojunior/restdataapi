import type { PontoGrafico } from '../../components/charts/types'
import { paraNumero } from '../../utils/format'
import type { EstoqueItem } from './types'

function somarPor(
  itens: EstoqueItem[],
  chave: (item: EstoqueItem) => string,
  campo: 'valor_atual' | 'quantidade',
): Map<string, number> {
  const mapa = new Map<string, number>()
  for (const item of itens) {
    const k = chave(item)
    const valor = campo === 'valor_atual' ? paraNumero(item.valor_atual) || 0 : Number(item.quantidade)
    mapa.set(k, (mapa.get(k) ?? 0) + valor)
  }
  return mapa
}

function topN(mapa: Map<string, number>, n: number): PontoGrafico[] {
  return [...mapa.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, n)
    .map(([rotulo, valor]) => ({ rotulo, valor }))
}

const rotuloProduto = (item: EstoqueItem) =>
  `${item.codigo_produto} — ${(item.descricao_produto ?? '').slice(0, 22)}`

export function topProdutosPorValor(itens: EstoqueItem[], n = 10): PontoGrafico[] {
  return topN(somarPor(itens, rotuloProduto, 'valor_atual'), n)
}

export function topProdutosPorQuantidade(itens: EstoqueItem[], n = 10): PontoGrafico[] {
  return topN(somarPor(itens, rotuloProduto, 'quantidade'), n)
}

export function valorPorFilial(itens: EstoqueItem[]): PontoGrafico[] {
  const mapa = somarPor(itens, (i) => i.filial, 'valor_atual')
  return [...mapa.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([rotulo, valor]) => ({ rotulo, valor }))
}

export function quantidadePorFilial(itens: EstoqueItem[]): PontoGrafico[] {
  const mapa = somarPor(itens, (i) => i.filial, 'quantidade')
  return [...mapa.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([rotulo, valor]) => ({ rotulo, valor }))
}
