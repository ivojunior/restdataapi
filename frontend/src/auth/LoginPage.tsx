import { Alert, Center, Image, Paper, Stack, Text, Title } from '@mantine/core'
import { IconAlertCircle } from '@tabler/icons-react'
import { useCallback } from 'react'
import { useAuth } from './AuthProvider'
import { useGoogleSignInButton } from './useGoogleIdentity'

export function LoginPage() {
  const { login, erroLogin } = useAuth()

  const handleCredential = useCallback(
    (credential: string) => {
      login(credential).catch(() => {
        // erro já fica exposto via erroLogin (renderizado abaixo); nada
        // mais a fazer aqui além de evitar uma promise rejeitada não tratada.
      })
    },
    [login],
  )

  const buttonRef = useGoogleSignInButton(handleCredential)

  return (
    <Center h="100vh" bg="gray.1">
      <Paper shadow="md" radius="md" p="xl" w={360}>
        <Stack align="center" gap="md">
          <Image src="/logo.jpg" h={46} w="auto" fit="contain" alt="Logotipo" />
          <Title order={3} ta="center">
            RestDataAPI
          </Title>
          <Text c="dimmed" size="sm" ta="center">
            Entre com sua conta Google da empresa para continuar.
          </Text>
          <div ref={buttonRef} />
          {erroLogin && (
            <Alert
              icon={<IconAlertCircle size={16} />}
              color="red"
              title="Não foi possível entrar"
              w="100%"
            >
              {erroLogin}
            </Alert>
          )}
        </Stack>
      </Paper>
    </Center>
  )
}
