import { hojeAAAAMMDD } from '../../utils/date'
import { categorizar } from './categorizacao'
import type { FinanceiroItem, FinanceiroItemEnriquecido, StatusFinanceiro } from './types'

/** Réplica de `_status_from_row` em client/app_financeiro.py. */
function calcularStatus(item: FinanceiroItem, hoje: string): StatusFinanceiro {
  const baixa = (item.data_baixa ?? '').trim()
  if (baixa) return 'Baixado'
  const vcto = (item.vencimento_real ?? '').trim()
  if (vcto && vcto < hoje) return 'Vencido'
  return 'Em aberto'
}

/** 'AAAAMMDD' -> 'AAAAMM' (chave ordenável); '' se a data for inválida —
 * réplica de `_mes_ano`. */
function calcularMesAno(vencimentoReal: string): string {
  const s = (vencimentoReal ?? '').trim()
  return s.length === 8 && /^\d+$/.test(s) ? s.slice(0, 6) : ''
}

/** Adiciona status/mesAno/categoria a cada item — mesmo cálculo que
 * `_on_data_ready` faz ao carregar os dados em client/app_financeiro.py. */
export function enriquecerItens(itens: FinanceiroItem[]): FinanceiroItemEnriquecido[] {
  const hoje = hojeAAAAMMDD()
  return itens.map((item) => ({
    ...item,
    status: calcularStatus(item, hoje),
    mesAno: calcularMesAno(item.vencimento_real),
    categoria: categorizar(item.nome_fornecedor, item.historico),
  }))
}

/** 'AAAAMM' -> 'MM/AAAA', para exibição — réplica de `_fmt_mes`. */
export function formatarMesAno(mesAno: string): string {
  return mesAno.length === 6 ? `${mesAno.slice(4, 6)}/${mesAno.slice(0, 4)}` : mesAno || '—'
}
