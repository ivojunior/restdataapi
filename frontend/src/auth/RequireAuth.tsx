import { Center, Loader } from '@mantine/core'
import type { ReactNode } from 'react'
import { useAuth } from './AuthProvider'
import { LoginPage } from './LoginPage'

/** Só renderiza `children` se houver uma sessão válida; caso contrário
 * mostra a tela de login (sem redirecionar para uma rota separada — a
 * própria ausência de sessão já "é" a tela de login). */
export function RequireAuth({ children }: { children: ReactNode }) {
  const { usuario, carregando } = useAuth()

  if (carregando) {
    return (
      <Center h="100vh">
        <Loader />
      </Center>
    )
  }

  if (!usuario) {
    return <LoginPage />
  }

  return <>{children}</>
}
