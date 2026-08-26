import { chaveCarga, STATUS_CARGA_FECHADO, type CargaItem } from './types'

export interface KpisCargas {
  totalCargas: number
  pedidos: number
  pesoTotal: number
  valorTotal: number
  valorAberto: number
  valorAcertado: number
  valorMedio: number
}

/** Réplica de `_update_kpis` em client/app_cargas.py. */
export function calcularKpis(itens: CargaItem[]): KpisCargas {
  const cargasDistintas = new Set(itens.map(chaveCarga))
  const totalCargas = cargasDistintas.size

  const valorTotal = itens.reduce((soma, i) => soma + Number(i.valor), 0)
  const valorAberto = itens
    .filter((i) => i.status_carga !== STATUS_CARGA_FECHADO)
    .reduce((soma, i) => soma + Number(i.valor), 0)

  return {
    totalCargas,
    pedidos: new Set(itens.map((i) => i.pedido)).size,
    pesoTotal: itens.reduce((soma, i) => soma + Number(i.peso), 0),
    valorTotal,
    valorAberto,
    valorAcertado: valorTotal - valorAberto,
    valorMedio: totalCargas ? valorTotal / totalCargas : 0,
  }
}
