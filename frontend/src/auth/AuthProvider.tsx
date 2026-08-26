import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { apiClient, ApiError } from '../api/client'

export interface UsuarioLogado {
  email: string
  nome: string
}

interface AuthContextValue {
  usuario: UsuarioLogado | null
  carregando: boolean
  erroLogin: string | null
  login: (credential: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<UsuarioLogado | null>(null)
  const [carregando, setCarregando] = useState(true)
  const [erroLogin, setErroLogin] = useState<string | null>(null)

  // No boot da SPA, tenta recuperar a sessão a partir do cookie (ex.: usuário
  // já logado numa aba/refresh anterior) — só então decide se mostra a tela
  // de login ou o app.
  useEffect(() => {
    apiClient
      .get<UsuarioLogado>('/auth/me')
      .then(setUsuario)
      .catch(() => setUsuario(null))
      .finally(() => setCarregando(false))
  }, [])

  const login = useCallback(async (credential: string) => {
    setErroLogin(null)
    try {
      const usuarioLogado = await apiClient.post<UsuarioLogado>('/auth/google', { credential })
      setUsuario(usuarioLogado)
    } catch (erro) {
      setUsuario(null)
      setErroLogin(
        erro instanceof ApiError && erro.status === 401
          ? 'Login não autorizado — verifique se você está usando uma conta do domínio da empresa.'
          : 'Não foi possível entrar em contato com o servidor. Tente novamente.',
      )
      throw erro
    }
  }, [])

  const logout = useCallback(async () => {
    await apiClient.post('/auth/logout')
    setUsuario(null)
  }, [])

  return (
    <AuthContext.Provider value={{ usuario, carregando, erroLogin, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const contexto = useContext(AuthContext)
  if (!contexto) {
    throw new Error('useAuth precisa ser usado dentro de <AuthProvider>')
  }
  return contexto
}
