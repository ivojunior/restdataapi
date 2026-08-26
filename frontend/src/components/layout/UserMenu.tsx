import { Avatar, Group, Menu, Text, UnstyledButton } from '@mantine/core'
import { IconChevronDown, IconLogout } from '@tabler/icons-react'
import { useAuth } from '../../auth/AuthProvider'

function iniciais(nome: string): string {
  return nome
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((parte) => parte[0]?.toUpperCase() ?? '')
    .join('')
}

export function UserMenu() {
  const { usuario, logout } = useAuth()
  if (!usuario) return null

  return (
    <Menu shadow="md" width={220} position="bottom-end">
      <Menu.Target>
        <UnstyledButton>
          <Group gap="xs" wrap="nowrap">
            <Avatar radius="xl" size="sm" color="primary">
              {iniciais(usuario.nome)}
            </Avatar>
            <div style={{ lineHeight: 1.1 }}>
              <Text size="sm" fw={500} visibleFrom="sm">
                {usuario.nome}
              </Text>
              <Text size="xs" c="dimmed" visibleFrom="sm">
                {usuario.email}
              </Text>
            </div>
            <IconChevronDown size={14} stroke={1.6} />
          </Group>
        </UnstyledButton>
      </Menu.Target>
      <Menu.Dropdown>
        <Menu.Item leftSection={<IconLogout size={16} />} color="red" onClick={() => void logout()}>
          Sair
        </Menu.Item>
      </Menu.Dropdown>
    </Menu>
  )
}
