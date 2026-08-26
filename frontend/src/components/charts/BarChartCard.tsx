import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { ChartCard } from './ChartCard'
import type { PontoGrafico } from './types'

export function BarChartCard({
  titulo, dados, formatarValor, corBarra = '#2980b9', corPorRotulo,
}: {
  titulo: string
  dados: PontoGrafico[]
  formatarValor: (v: number) => string
  corBarra?: string
  /** Opcional — quando presente, decide a cor de cada barra pelo rótulo
   * (sobrepõe corBarra), ex.: vermelho/azul por mês vencido/a vencer em
   * client/app_financeiro.py. */
  corPorRotulo?: (rotulo: string | number) => string
}) {
  return (
    <ChartCard titulo={titulo}>
      <ResponsiveContainer>
        <BarChart data={dados} margin={{ left: 8, right: 8, top: 4, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="rotulo" fontSize={11} />
          <YAxis tickFormatter={formatarValor} fontSize={11} width={70} />
          <Tooltip formatter={(valor) => formatarValor(Number(valor))} />
          <Bar dataKey="valor" fill={corBarra} radius={[4, 4, 0, 0]}>
            {corPorRotulo && dados.map((ponto, i) => <Cell key={i} fill={corPorRotulo(ponto.rotulo)} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  )
}
