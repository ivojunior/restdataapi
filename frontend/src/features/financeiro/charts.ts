import type { PontoGrafico } from '../../components/charts/types'
import { hojeAAAAMMDD } from '../../utils/date'
import { formatarMesAno } from './enriquecimento'
import type { FinanceiroItemEnriquecido } from './types'

function agruparSoma(
  itens: FinanceiroItemEnriquecido[],
  chaveDe: (item: FinanceiroItemEnriquecido) => string,
  campo: 'valor' | 'saldo',
): Map<string, number> {
  const mapa = new Map<string, number>()
  for (const item of itens) {
    const chave = chaveDe(item)
    mapa.set(chave, (mapa.get(chave) ?? 0) + Number(item[campo]))
  }
  return mapa
}

/** Réplica de `status_counts = df["status"].value_counts()` — contagem de
 * títulos por status, do mais frequente para o menos frequente. */
export function distribuicaoPorStatus(itens: FinanceiroItemEnriquecido[]): PontoGrafico[] {
  const mapa = new Map<string, number>()
  for (const item of itens) mapa.set(item.status, (mapa.get(item.status) ?? 0) + 1)
  return [...mapa.entries()].sort((a, b) => b[1] - a[1]).map(([rotulo, valor]) => ({ rotulo, valor }))
}

/** Top 10 fornecedores por saldo — réplica do bloco `top10` em `_update_charts`. */
export function topFornecedoresPorSaldo(itens: FinanceiroItemEnriquecido[], n = 10): PontoGrafico[] {
  const mapa = agruparSoma(itens, (i) => i.nome_fornecedor ?? '(sem nome)', 'saldo')
  return [...mapa.entries()].sort((a, b) => b[1] - a[1]).slice(0, n).map(([rotulo, valor]) => ({ rotulo, valor }))
}

/** Saldo por mês de vencimento (títulos não baixados), últimos 14 meses —
 * réplica do bloco `by_month` em `_update_charts`. */
export function saldoPorMesVencimento(itens: FinanceiroItemEnriquecido[], n = 14): PontoGrafico[] {
  const abertos = itens.filter((i) => i.status !== 'Baixado')
  const mapa = agruparSoma(abertos, (i) => i.mesAno, 'saldo')
  mapa.delete('')
  return [...mapa.entries()]
    .sort((a, b) => a[0].localeCompare(b[0]))
    .slice(-n)
    .map(([mes, valor]) => ({ rotulo: formatarMesAno(mes), valor }))
}

/** Cor de cada barra de `saldoPorMesVencimento`: vermelho para meses já
 * vencidos (mês < mês corrente), azul para "a vencer" — réplica de
 * `bar_clrs_mes` em `_update_charts`. Recebe o rótulo já formatado
 * (MM/AAAA), por isso reconverte para AAAAMM antes de comparar. */
export function corSaldoPorMes(rotuloMesAno: string | number): string {
  const s = String(rotuloMesAno)
  const mesAno = s.length === 7 ? `${s.slice(3, 7)}${s.slice(0, 2)}` : ''
  return mesAno && mesAno < hojeAAAAMMDD().slice(0, 6) ? '#e74c3c' : '#2980b9'
}

/** Saldo por tipo de operação, top 10 — réplica do bloco `by_tipo` em
 * `_update_charts`. */
export function saldoPorTipoOperacao(itens: FinanceiroItemEnriquecido[], n = 10): PontoGrafico[] {
  const mapa = agruparSoma(itens, (i) => i.descricao_operacao ?? '(não informado)', 'saldo')
  return [...mapa.entries()].sort((a, b) => b[1] - a[1]).slice(0, n).map(([rotulo, valor]) => ({ rotulo, valor }))
}
