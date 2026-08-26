import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { ChartCard } from './ChartCard'
import type { PontoGrafico } from './types'

export function BarChartCard({
  titulo, dados, formatarValor, corBarra = '#2980b9',
}: {
  titulo: string
  dados: PontoGrafico[]
  formatarValor: (v: number) => string
  corBarra?: string
}) {
  return (
    <ChartCard titulo={titulo}>
      <ResponsiveContainer>
        <BarChart data={dados} margin={{ left: 8, right: 8, top: 4, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="rotulo" fontSize={11} />
          <YAxis tickFormatter={formatarValor} fontSize={11} width={70} />
          <Tooltip formatter={(valor) => formatarValor(Number(valor))} />
          <Bar dataKey="valor" fill={corBarra} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  )
}
