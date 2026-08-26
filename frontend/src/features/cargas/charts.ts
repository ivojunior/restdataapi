import type { PontoGrafico } from '../../components/charts/types'
import { formatarDataBR } from '../../utils/format'
import { chaveCarga, type CargaItem } from './types'

function rotuloCliente(codigo: string, nome: string | null): string {
  const cod = (codigo || '').trim().slice(0, 6)
  const nom = (nome || '(sem nome)').trim().slice(0, 16)
  return `${cod}-${nom}`
}

/** Réplica de `top_clientes` em `_update_charts` (client/app_cargas.py):
 * agrupa por (cliente, nome_cliente), soma valor, top 10. */
export function topClientesPorValor(itens: CargaItem[], n = 10): PontoGrafico[] {
  const mapa = new Map<string, { rotulo: string; valor: number }>()
  for (const item of itens) {
    const chave = `${item.cliente}|${item.nome_cliente ?? ''}`
    const atual = mapa.get(chave)
    const valor = (atual?.valor ?? 0) + Number(item.valor)
    mapa.set(chave, { rotulo: rotuloCliente(item.cliente, item.nome_cliente), valor })
  }
  return [...mapa.values()]
    .sort((a, b) => b.valor - a.valor)
    .slice(0, n)
    .map(({ rotulo, valor }) => ({ rotulo, valor }))
}

export function valorPorFilial(itens: CargaItem[]): PontoGrafico[] {
  const mapa = new Map<string, number>()
  for (const item of itens) {
    mapa.set(item.filial, (mapa.get(item.filial) ?? 0) + Number(item.valor))
  }
  return [...mapa.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([rotulo, valor]) => ({ rotulo, valor }))
}

/** Nº de cargas DISTINTAS (não itens) por data, últimas 12 datas — réplica
 * de `by_data` em `_update_charts`. */
export function cargasPorData(itens: CargaItem[], n = 12): PontoGrafico[] {
  const mapa = new Map<string, Set<string>>()
  for (const item of itens) {
    const conjunto = mapa.get(item.data) ?? new Set<string>()
    conjunto.add(chaveCarga(item))
    mapa.set(item.data, conjunto)
  }
  return [...mapa.entries()]
    .sort((a, b) => a[0].localeCompare(b[0]))
    .slice(-n)
    .map(([data, cargas]) => ({ rotulo: formatarDataBR(data), valor: cargas.size }))
}

export function topCaminhoesPorPeso(itens: CargaItem[], n = 10): PontoGrafico[] {
  const mapa = new Map<string, number>()
  for (const item of itens) {
    mapa.set(item.caminhao, (mapa.get(item.caminhao) ?? 0) + Number(item.peso))
  }
  return [...mapa.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, n)
    .map(([rotulo, valor]) => ({ rotulo, valor }))
}
