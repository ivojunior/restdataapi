import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { ChartCard } from './ChartCard'
import { CORES_GRAFICO } from './colors'
import type { PontoGrafico } from './types'

/** Barras horizontais — usado para os "Top N" (por faturamento, por lucro
 * etc.), réplica dos `ax.barh(...)` do client desktop. Espera `dados` já
 * ordenado do maior para o menor valor (maior barra no topo). */
export function HBarChart({
  titulo, dados, formatarValor, corPorRotulo,
}: {
  titulo: string
  dados: PontoGrafico[]
  formatarValor: (v: number) => string
  /** Opcional — mesma ideia de PieChartCard.corPorRotulo. */
  corPorRotulo?: (rotulo: string | number) => string
}) {
  return (
    <ChartCard titulo={titulo}>
      <ResponsiveContainer>
        <BarChart data={dados} layout="vertical" margin={{ left: 8, right: 48, top: 4, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} />
          <XAxis type="number" tickFormatter={formatarValor} fontSize={11} />
          <YAxis type="category" dataKey="rotulo" width={150} fontSize={11} interval={0} />
          <Tooltip formatter={(valor) => formatarValor(Number(valor))} />
          <Bar dataKey="valor" radius={[0, 4, 4, 0]}>
            {dados.map((ponto, i) => (
              <Cell key={i} fill={corPorRotulo ? corPorRotulo(ponto.rotulo) : CORES_GRAFICO[i % CORES_GRAFICO.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  )
}
