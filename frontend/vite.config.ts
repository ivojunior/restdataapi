import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Prefixos das rotas da API FastAPI (ver app/main.py) — em dev, o servidor
// Vite (porta 5173) faz proxy para o backend (porta 8000) nesses caminhos,
// para que o browser enxergue tudo como mesma origem (cookie de sessão
// httpOnly funciona sem CORS cross-site). Em produção, a SPA é servida pelo
// próprio FastAPI, então esse proxy não é necessário (mesma origem real).
const API_PREFIXES = [
  '/auth', '/cargas', '/faturamento', '/financeiro', '/fornecedores',
  '/produtos', '/saldos-estoque', '/titulos-pagar', '/health',
]

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: Object.fromEntries(
      API_PREFIXES.map((prefix) => [
        prefix,
        { target: 'http://localhost:8000', changeOrigin: true },
      ]),
    ),
  },
})
