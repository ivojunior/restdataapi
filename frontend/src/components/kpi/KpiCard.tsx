import { Paper, Text } from '@mantine/core'

export function KpiCard({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <Paper withBorder radius="md" p="sm" ta="center">
      <Text size="xs" c="dimmed">
        {label}
      </Text>
      <Text size="lg" fw={700} c={color}>
        {value}
      </Text>
    </Paper>
  )
}
