// Base vazia: a SPA é servida pelo próprio FastAPI (mesma origem) em
// produção, e em dev o proxy do Vite (ver vite.config.ts) encaminha os
// mesmos caminhos para o backend — nunca precisamos de uma URL absoluta.
const BASE_URL = ''

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const resposta = await fetch(`${BASE_URL}${path}`, {
    ...init,
    // Sem isto, o browser não envia o cookie httpOnly de sessão em
    // requisições cross-origin (ex.: SPA em localhost:5173, API em
    // localhost:8000 durante o dev, mesmo com o proxy do Vite reescrevendo
    // a origem "vista" pelo browser).
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...init.headers },
  })

  if (!resposta.ok) {
    let detail = resposta.statusText
    try {
      const corpo = await resposta.json()
      detail = corpo.detail ?? detail
    } catch {
      // corpo não é JSON (ex.: 404 de um proxy) — mantém statusText
    }
    throw new ApiError(resposta.status, detail)
  }

  if (resposta.status === 204) {
    return undefined as T
  }
  return (await resposta.json()) as T
}

export const apiClient = {
  get: <T>(path: string): Promise<T> => request<T>(path, { method: 'GET' }),
  post: <T>(path: string, body?: unknown): Promise<T> =>
    request<T>(path, {
      method: 'POST',
      body: body === undefined ? undefined : JSON.stringify(body),
    }),
}
