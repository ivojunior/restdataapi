import { SimpleGrid } from '@mantine/core'
import type { ReactNode } from 'react'

export function KpiRow({ children }: { children: ReactNode }) {
  return (
    <SimpleGrid cols={{ base: 2, xs: 3, sm: 3, md: 5, lg: 9 }} spacing="xs">
      {children}
    </SimpleGrid>
  )
}
