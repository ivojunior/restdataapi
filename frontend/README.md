# RestDataAPI — frontend (SPA)

SPA React + TypeScript + Vite que consome a RestDataAPI, autenticando via login Google Workspace (ver `app/routers/auth.py` no backend, e a seção "Login via Google Workspace (SPA)" no `README.md` da raiz).

## Stack

- **React 18 + TypeScript + Vite** — sem SSR (não é necessário: app interno, atrás de login).
- **Mantine UI** — componentes responsivos (drawer mobile, tabelas, cards); tema em `src/theme.ts`, mapeado da paleta já usada nos clients desktop.
- **React Router** — roteamento client-side (`BrowserRouter`).
- **TanStack Query** — cache/estado de dados assíncronos.
- **Recharts** — gráficos (barras, pizza), adicionado na Fase 3 (piloto de Faturamento).
- **Google Identity Services** — carregado sob demanda em `src/auth/useGoogleIdentity.ts`, só quando a tela de login é montada.

## Desenvolvimento local

1. Instale as dependências:
   ```bash
   npm install
   ```
2. Copie o arquivo de exemplo de variáveis de ambiente e preencha o Client ID OAuth (ver "Configuração" no `README.md` da raiz para como criá-lo no Google Cloud Console):
   ```bash
   cp .env.example .env
   ```
3. Com a API rodando em `http://localhost:8000` (`uvicorn app.main:app --reload`, na raiz do projeto), inicie o dev server:
   ```bash
   npm run dev
   ```
   O Vite (porta padrão `5173`) faz proxy de `/auth`, `/faturamento`, `/cargas`, `/financeiro`, `/saldos-estoque`, `/fornecedores`, `/produtos`, `/titulos-pagar` e `/health` para a API em `localhost:8000` (ver `vite.config.ts`) — o browser enxerga tudo como mesma origem, então o cookie de sessão funciona normalmente em dev.

## Build de produção

```bash
npm run build
```

Gera `dist/`, servido pelo próprio FastAPI em produção (`app/main.py` monta `dist/` em `/` quando o diretório existe — ver comentário lá). O `Dockerfile` da raiz já builda este projeto num estágio Node separado antes de montar a imagem final da API.

## Estrutura

```
src/
├── api/               # cliente HTTP (fetch com credentials:'include'), tipos comuns (PaginatedResponse)
├── auth/               # AuthProvider, LoginPage, RequireAuth, integração com o Google Identity Services
├── components/          # componentes genéricos, escritos uma vez e reaproveitados por cada feature/relatório
│   ├── layout/            # AppLayout (Mantine AppShell), Header, UserMenu
│   ├── kpi/                # KpiCard, KpiRow (grid responsivo)
│   ├── charts/              # HBarChart, PieChartCard, BarChartCard (Recharts) + paleta/tipos compartilhados
│   ├── data-table/           # ResponsiveTable — tabela ordenável no desktop, cards empilhados no mobile
│   └── export/                # ExportExcelButton — link para um endpoint /*/export do backend
├── features/            # um diretório por relatório, só com o que é específico dele
│   └── faturamento/       # completo (piloto da migração) — Page, hook de dados, kpis.ts, charts.ts, api.ts
├── pages/                # placeholders "em construção" para os relatórios ainda não portados (Cargas, Financeiro, Estoque)
└── theme.ts               # tema Mantine com a paleta de cores do projeto
```

Padrão-chave: tudo em `components/` é genérico (recebe dados/config via props) e não conhece nenhum relatório específico — cada `features/<relatorio>/` só fornece os dados e a configuração (colunas da tabela, séries dos gráficos, fórmulas de KPI). Ao portar o próximo relatório (Cargas, Financeiro ou Estoque), o trabalho é escrever um novo `features/<relatorio>/` seguindo o padrão de `features/faturamento/`, não criar novos componentes de UI do zero.
