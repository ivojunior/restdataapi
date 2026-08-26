import { Center, Stack, Text, ThemeIcon, Title } from '@mantine/core'
import type { IconProps } from '@tabler/icons-react'
import type { ComponentType } from 'react'

type TablerIcon = ComponentType<IconProps>

/** Placeholder genérico para as páginas de relatório ainda não implementadas
 * (Fases 3-6 do plano) — evita duplicar o mesmo markup em cada página. */
export function EmConstrucao({ titulo, icon: Icone }: { titulo: string; icon: TablerIcon }) {
  return (
    <Center h="60vh">
      <Stack align="center" gap="xs">
        <ThemeIcon size={64} radius="xl" variant="light" color="primary">
          <Icone size={32} stroke={1.5} />
        </ThemeIcon>
        <Title order={3}>{titulo}</Title>
        <Text c="dimmed">Em construção — chegando em uma próxima fase.</Text>
      </Stack>
    </Center>
  )
}
