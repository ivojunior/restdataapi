import { Group, Image, Text } from '@mantine/core'

export function Header() {
  return (
    <Group gap="xs" wrap="nowrap">
      <Image src="/logo.jpg" h={34} w="auto" fit="contain" alt="Logotipo" />
      <Text fw={700} c="primary.8" visibleFrom="xs">
        RestDataAPI
      </Text>
    </Group>
  )
}
