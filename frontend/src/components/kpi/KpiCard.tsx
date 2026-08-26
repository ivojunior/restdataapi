import { Paper, Text } from '@mantine/core'

export function KpiCard({
  label, value, color, sublinha,
}: {
  label: string
  value: string
  color?: string
  /** Segunda linha opcional, menor, abaixo do valor principal — ex.
   * "Em Aberto" no Financeiro mostra a contagem de títulos (value) e o
   * saldo (sublinha) — réplica do `"\n" + _brl(...)` dos KPIs de dois
   * valores em client/app_financeiro.py. */
  sublinha?: string
}) {
  return (
    <Paper withBorder radius="md" p="sm" ta="center">
      <Text size="xs" c="dimmed">
        {label}
      </Text>
      <Text size="lg" fw={700} c={color}>
        {value}
      </Text>
      {sublinha && (
        <Text size="sm" fw={600} c={color}>
          {sublinha}
        </Text>
      )}
    </Paper>
  )
}
