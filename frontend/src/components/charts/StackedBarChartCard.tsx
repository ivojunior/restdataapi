import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { ChartCard } from './ChartCard'

export interface SerieEmpilhada {
  chave: string
  nome: string
  cor: string
}

/** Barras empilhadas com múltiplas séries (ex.: valor por mês x categoria,
 * ou por dia x status) — cada linha de `dados` é um ponto no eixo X com uma
 * chave por série, mais o campo do próprio eixo X. Genérico o bastante para
 * qualquer número de séries (o piloto/Estoque/Cargas não precisavam disso —
 * só usam uma série por gráfico). */
export function StackedBarChartCard<T extends Record<string, unknown>>({
  titulo, dados, eixoX, series, formatarValor, altura = 320,
}: {
  titulo: string
  dados: T[]
  eixoX: string
  series: SerieEmpilhada[]
  formatarValor: (v: number) => string
  altura?: number
}) {
  return (
    <ChartCard titulo={titulo} altura={altura}>
      <ResponsiveContainer>
        <BarChart data={dados} margin={{ left: 8, right: 8, top: 4, bottom: 40 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey={eixoX} fontSize={11} angle={-40} textAnchor="end" interval={0} height={60} />
          <YAxis tickFormatter={formatarValor} fontSize={11} width={70} />
          <Tooltip formatter={(valor) => formatarValor(Number(valor))} />
          <Legend />
          {series.map((serie) => (
            <Bar key={serie.chave} dataKey={serie.chave} name={serie.nome} stackId="pilha" fill={serie.cor} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  )
}
