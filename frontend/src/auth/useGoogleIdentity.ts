import { useEffect, useRef } from 'react'

interface GoogleCredentialResponse {
  credential: string
}

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string
            callback: (response: GoogleCredentialResponse) => void
          }) => void
          renderButton: (parent: HTMLElement, options: Record<string, unknown>) => void
        }
      }
    }
  }
}

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined
const GSI_SCRIPT_SRC = 'https://accounts.google.com/gsi/client'
const GSI_SCRIPT_ID = 'google-identity-services'

function carregarScriptGoogle(): Promise<void> {
  if (window.google?.accounts?.id) {
    return Promise.resolve()
  }

  const existente = document.getElementById(GSI_SCRIPT_ID)
  if (existente) {
    return new Promise((resolve) => existente.addEventListener('load', () => resolve()))
  }

  return new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.id = GSI_SCRIPT_ID
    script.src = GSI_SCRIPT_SRC
    script.async = true
    script.defer = true
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('Falha ao carregar o script do Google Identity Services'))
    document.head.appendChild(script)
  })
}

/** Carrega o script do Google Identity Services sob demanda (só quando a
 * tela de login é montada, não no boot da SPA) e renderiza o botão "Sign in
 * with Google" dentro do elemento apontado pela ref retornada. */
export function useGoogleSignInButton(onCredential: (credential: string) => void) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) {
      // eslint-disable-next-line no-console
      console.error('VITE_GOOGLE_CLIENT_ID não configurado — login Google desabilitado.')
      return
    }

    let cancelado = false

    carregarScriptGoogle()
      .then(() => {
        if (cancelado || !containerRef.current || !window.google) return
        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: (response) => onCredential(response.credential),
        })
        window.google.accounts.id.renderButton(containerRef.current, {
          theme: 'outline',
          size: 'large',
          text: 'signin_with',
          shape: 'rectangular',
        })
      })
      .catch((erro: Error) => {
        // eslint-disable-next-line no-console
        console.error(erro)
      })

    return () => {
      cancelado = true
    }
  }, [onCredential])

  return containerRef
}
