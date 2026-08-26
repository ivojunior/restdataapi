import { Paper, Text } from '@mantine/core'
import type { ReactNode } from 'react'

export function ChartCard({
  titulo, children, altura = 280,
}: { titulo: string; children: ReactNode; altura?: number }) {
  return (
    <Paper withBorder radius="md" p="md">
      <Text fw={600} size="sm" mb="xs">
        {titulo}
      </Text>
      <div style={{ width: '100%', height: altura }}>{children}</div>
    </Paper>
  )
}
