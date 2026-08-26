import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { ChartCard } from './ChartCard'
import { CORES_GRAFICO } from './colors'
import type { PontoGrafico } from './types'

export function PieChartCard({
  titulo, dados, formatarValor, corPorRotulo,
}: {
  titulo: string
  dados: PontoGrafico[]
  formatarValor: (v: number) => string
  /** Opcional — quando presente, decide a cor de cada fatia pelo rótulo em
   * vez de ciclar CORES_GRAFICO (ex.: mapear status/categoria sempre para a
   * mesma cor, como em client/app_financeiro.py). */
  corPorRotulo?: (rotulo: string | number) => string
}) {
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
            {dados.map((ponto, i) => (
              <Cell key={i} fill={corPorRotulo ? corPorRotulo(ponto.rotulo) : CORES_GRAFICO[i % CORES_GRAFICO.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(valor) => formatarValor(Number(valor))} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </ChartCard>
  )
}
