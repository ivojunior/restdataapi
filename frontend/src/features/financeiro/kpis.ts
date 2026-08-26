import type { FinanceiroItemEnriquecido } from './types'

export interface KpisFinanceiro {
  totalTitulos: number
  valorTotal: number
  recuperacaoJudicial: number
  saldoTotal: number
  emAbertoQtd: number
  emAbertoSaldo: number
  vencidosQtd: number
  vencidosSaldo: number
  baixadosQtd: number
  baixadosValor: number
}

const ehRecuperacaoJudicial = (item: FinanceiroItemEnriquecido) =>
  (item.recuperacao_judicial ?? '').trim() === '1'

/** Réplica de `_update_kpis` em client/app_financeiro.py — títulos de
 * recuperação judicial somam à parte (`recuperacaoJudicial`) e ficam de
 * fora de saldoTotal/emAberto/vencidos (mas não de baixados, que usam o df
 * inteiro, sem excluir RJ — mesma assimetria do original). */
export function calcularKpis(itens: FinanceiroItemEnriquecido[]): KpisFinanceiro {
  const rj = itens.filter(ehRecuperacaoJudicial)
  const naoRj = itens.filter((i) => !ehRecuperacaoJudicial(i))

  const emAberto = naoRj.filter((i) => i.status === 'Em aberto')
  const vencidos = naoRj.filter((i) => i.status === 'Vencido')
  const baixados = itens.filter((i) => i.status === 'Baixado')

  const somar = (lista: FinanceiroItemEnriquecido[], campo: 'valor' | 'saldo') =>
    lista.reduce((soma, i) => soma + Number(i[campo]), 0)

  return {
    totalTitulos: itens.length,
    valorTotal: somar(itens, 'valor'),
    recuperacaoJudicial: somar(rj, 'valor'),
    saldoTotal: somar(naoRj, 'saldo'),
    emAbertoQtd: emAberto.length,
    emAbertoSaldo: somar(emAberto, 'saldo'),
    vencidosQtd: vencidos.length,
    vencidosSaldo: somar(vencidos, 'saldo'),
    baixadosQtd: baixados.length,
    baixadosValor: somar(baixados, 'valor'),
  }
}
