import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { ChartCard } from './ChartCard'
import { CORES_GRAFICO } from './colors'
import type { PontoGrafico } from './types'

export function PieChartCard({
  titulo, dados, formatarValor,
}: { titulo: string; dados: PontoGrafico[]; formatarValor: (v: number) => string }) {
  return (
    <ChartCard titulo={titulo}>
      <ResponsiveContainer>
        <PieChart>
          <Pie
            data={dados}
            dataKey="valor"
            nameKey="rotulo"
            outerRadius="75%"
            label={(props: { percent?: number }) => `${((props.percent ?? 0) * 100).toFixed(1)}%`}
          >
            {dados.map((_, i) => (
              <Cell key={i} fill={CORES_GRAFICO[i % CORES_GRAFICO.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(valor) => formatarValor(Number(valor))} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </ChartCard>
  )
}
