import { AppShell, Burger, Group, NavLink, ScrollArea } from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import {
  IconBoxSeam, IconFileInvoice, IconReceipt2, IconTruck,
} from '@tabler/icons-react'
import type { ReactNode } from 'react'
import { NavLink as RouterNavLink, useLocation } from 'react-router-dom'
import { Header } from './Header'
import { UserMenu } from './UserMenu'

const NAV_ITEMS = [
  { to: '/faturamento', label: 'Faturamento', icon: IconFileInvoice },
  { to: '/cargas', label: 'Cargas', icon: IconTruck },
  { to: '/financeiro', label: 'Financeiro', icon: IconReceipt2 },
  { to: '/estoque', label: 'Estoque', icon: IconBoxSeam },
]

export function AppLayout({ children }: { children: ReactNode }) {
  const [opened, { toggle, close }] = useDisclosure()
  const location = useLocation()

  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{ width: 240, breakpoint: 'sm', collapsed: { mobile: !opened } }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between" wrap="nowrap">
          <Group gap="sm" wrap="nowrap">
            <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
            <Header />
          </Group>
          <UserMenu />
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="xs">
        <ScrollArea>
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              component={RouterNavLink}
              to={item.to}
              label={item.label}
              leftSection={<item.icon size={18} stroke={1.6} />}
              active={location.pathname.startsWith(item.to)}
              onClick={close}
            />
          ))}
        </ScrollArea>
      </AppShell.Navbar>

      <AppShell.Main>{children}</AppShell.Main>
    </AppShell>
  )
}
