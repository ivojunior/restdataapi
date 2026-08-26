import type { SerieEmpilhada } from '../../components/charts/StackedBarChartCard'
import type { PontoGrafico } from '../../components/charts/types'
import { formatarBRL, formatarDataBR } from '../../utils/format'
import { corDaCategoria } from './categoriaCores'
import { formatarMesAno } from './enriquecimento'
import { STATUS_CORES, type FinanceiroItemEnriquecido } from './types'

export interface ResumoCategoriaLinha {
  categoria: string
  qtd: number
  valorTotal: number
  pct: number
  valorMedio: number
}

/** Réplica de `_update_categoria_view` — tabela (linhas + total geral) e
 * dados do gráfico "Valor Total por Categoria". */
export function resumoPorCategoria(itens: FinanceiroItemEnriquecido[]): {
  linhas: ResumoCategoriaLinha[]
  total: ResumoCategoriaLinha
  grafico: PontoGrafico[]
} {
  const mapa = new Map<string, { qtd: number; valorTotal: number }>()
  for (const item of itens) {
    const atual = mapa.get(item.categoria) ?? { qtd: 0, valorTotal: 0 }
    atual.qtd += 1
    atual.valorTotal += Number(item.valor)
    mapa.set(item.categoria, atual)
  }
  const totalGeral = itens.reduce((s, i) => s + Number(i.valor), 0)

  const linhas = [...mapa.entries()]
    .map(([categoria, { qtd, valorTotal }]) => ({
      categoria,
      qtd,
      valorTotal,
      pct: totalGeral ? (valorTotal / totalGeral) * 100 : 0,
      valorMedio: qtd ? valorTotal / qtd : 0,
    }))
    .sort((a, b) => b.valorTotal - a.valorTotal)

  return {
    linhas,
    total: {
      categoria: 'TOTAL GERAL',
      qtd: itens.length,
      valorTotal: totalGeral,
      pct: 100,
      valorMedio: 0,
    },
    grafico: linhas.map((l) => ({ rotulo: l.categoria, valor: l.valorTotal })),
  }
}

export interface ResumoFilialLinha {
  filial: string
  qtd: number
  valorTotal: number
  pct: number
}

/** Réplica de `_update_filial_view`. */
export function resumoPorFilial(itens: FinanceiroItemEnriquecido[]): {
  linhas: ResumoFilialLinha[]
  total: ResumoFilialLinha
  grafico: PontoGrafico[]
} {
  const mapa = new Map<string, { qtd: number; valorTotal: number }>()
  for (const item of itens) {
    const atual = mapa.get(item.filial) ?? { qtd: 0, valorTotal: 0 }
    atual.qtd += 1
    atual.valorTotal += Number(item.valor)
    mapa.set(item.filial, atual)
  }
  const totalGeral = itens.reduce((s, i) => s + Number(i.valor), 0)

  const linhas = [...mapa.entries()]
    .map(([filial, { qtd, valorTotal }]) => ({
      filial,
      qtd,
      valorTotal,
      pct: totalGeral ? (valorTotal / totalGeral) * 100 : 0,
    }))
    .sort((a, b) => b.valorTotal - a.valorTotal)

  return {
    linhas,
    total: { filial: 'TOTAL GERAL', qtd: itens.length, valorTotal: totalGeral, pct: 100 },
    grafico: linhas.map((l) => ({ rotulo: l.filial, valor: l.valorTotal })),
  }
}

export interface ResumoEvolucao {
  colunasMes: { mesAno: string; titulo: string }[]
  linhas: Record<string, string>[]
  linhaTotal: Record<string, string>
  graficoDados: Record<string, unknown>[]
  graficoSeries: SerieEmpilhada[]
}

/** Réplica de `_update_evolucao_view` — pivô categoria x mês (tabela) e o
 * inverso, mês x categoria empilhado (gráfico), a partir da mesma
 * agregação `categoria x mesAno -> soma(valor)`. */
export function resumoEvolucaoMensal(itens: FinanceiroItemEnriquecido[]): ResumoEvolucao {
  const meses = [...new Set(itens.map((i) => i.mesAno).filter(Boolean))].sort()
  const porCategoriaMes = new Map<string, Map<string, number>>()
  for (const item of itens) {
    if (!item.mesAno) continue
    const porMes = porCategoriaMes.get(item.categoria) ?? new Map<string, number>()
    porMes.set(item.mesAno, (porMes.get(item.mesAno) ?? 0) + Number(item.valor))
    porCategoriaMes.set(item.categoria, porMes)
  }

  const categoriasComTotal = [...porCategoriaMes.entries()]
    .map(([categoria, porMes]) => ({
      categoria,
      porMes,
      total: [...porMes.values()].reduce((s, v) => s + v, 0),
    }))
    .sort((a, b) => b.total - a.total)

  const colunasMes = meses.map((mesAno) => ({ mesAno, titulo: formatarMesAno(mesAno) }))

  const linhas = categoriasComTotal.map(({ categoria, porMes, total }) => {
    const linha: Record<string, string> = { categoria }
    for (const mesAno of meses) linha[mesAno] = formatarBRL(porMes.get(mesAno) ?? 0)
    linha.total = formatarBRL(total)
    return linha
  })

  const linhaTotal: Record<string, string> = { categoria: 'TOTAL MENSAL' }
  let totalGeral = 0
  for (const mesAno of meses) {
    const somaMes = categoriasComTotal.reduce((s, c) => s + (c.porMes.get(mesAno) ?? 0), 0)
    linhaTotal[mesAno] = formatarBRL(somaMes)
    totalGeral += somaMes
  }
  linhaTotal.total = formatarBRL(totalGeral)

  const graficoDados = meses.map((mesAno) => {
    const ponto: Record<string, unknown> = { mes: formatarMesAno(mesAno) }
    for (const { categoria, porMes } of categoriasComTotal) ponto[categoria] = porMes.get(mesAno) ?? 0
    return ponto
  })
  const graficoSeries: SerieEmpilhada[] = categoriasComTotal.map(({ categoria }) => ({
    chave: categoria,
    nome: categoria,
    cor: corDaCategoria(categoria),
  }))

  return { colunasMes, linhas, linhaTotal, graficoDados, graficoSeries }
}

export interface ResumoDia {
  linhas: Record<string, string>[]
  linhaTotal: Record<string, string>
  graficoDados: Record<string, unknown>[]
  graficoSeries: SerieEmpilhada[]
}

const STATUS_PIVO = ['Em aberto', 'Vencido', 'Baixado'] as const

/** Réplica de `_update_dia_view` — "Em aberto"/"Vencido" somam saldo,
 * "Baixado" soma valor (mesma convenção de calcularKpis), pivotado por dia
 * de vencimento. Sem corte de "últimos N dias", de propósito (mesmo
 * comentário do original): o volume já é limitado pelo filtro de período
 * do servidor. */
export function resumoTotalPorDia(itens: FinanceiroItemEnriquecido[]): ResumoDia {
  const porDia = new Map<string, Record<(typeof STATUS_PIVO)[number], number>>()
  for (const item of itens) {
    const dia = item.vencimento_real
    const registro = porDia.get(dia) ?? { 'Em aberto': 0, Vencido: 0, Baixado: 0 }
    const valorConsiderado = item.status === 'Baixado' ? Number(item.valor) : Number(item.saldo)
    registro[item.status] += valorConsiderado
    porDia.set(dia, registro)
  }

  const dias = [...porDia.keys()].sort()

  const linhas = dias.map((dia) => {
    const registro = porDia.get(dia)!
    const total = STATUS_PIVO.reduce((s, status) => s + registro[status], 0)
    return {
      dia: formatarDataBR(dia),
      emAberto: formatarBRL(registro['Em aberto']),
      vencido: formatarBRL(registro.Vencido),
      baixado: formatarBRL(registro.Baixado),
      total: formatarBRL(total),
    }
  })

  const somaStatus = (status: (typeof STATUS_PIVO)[number]) =>
    dias.reduce((s, dia) => s + porDia.get(dia)![status], 0)
  const totalGeral = STATUS_PIVO.reduce((s, status) => s + somaStatus(status), 0)
  const linhaTotal = {
    dia: 'TOTAL',
    emAberto: formatarBRL(somaStatus('Em aberto')),
    vencido: formatarBRL(somaStatus('Vencido')),
    baixado: formatarBRL(somaStatus('Baixado')),
    total: formatarBRL(totalGeral),
  }

  const graficoDados = dias.map((dia) => {
    const registro = porDia.get(dia)!
    return { dia: formatarDataBR(dia).slice(0, 5), ...registro }
  })
  const graficoSeries: SerieEmpilhada[] = STATUS_PIVO.map((status) => ({
    chave: status,
    nome: status,
    cor: STATUS_CORES[status],
  }))

  return { linhas, linhaTotal, graficoDados, graficoSeries }
}
