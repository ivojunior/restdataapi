# RestDataAPI — frontend (SPA)

SPA React + TypeScript + Vite que consome a RestDataAPI, autenticando via login Google Workspace (ver `app/routers/auth.py` no backend, e a seção "Login via Google Workspace (SPA)" no `README.md` da raiz).

## Stack

- **React 18 + TypeScript + Vite** — sem SSR (não é necessário: app interno, atrás de login).
- **Mantine UI** — componentes responsivos (drawer mobile, tabelas, cards); tema em `src/theme.ts`, mapeado da paleta já usada nos clients desktop.
- **React Router** — roteamento client-side (`BrowserRouter`).
- **TanStack Query** — cache/estado de dados assíncronos.
- **Recharts** — gráficos (barras, pizza, barras empilhadas), adicionado na Fase 3 (piloto de Faturamento).
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
│   ├── kpi/                # KpiCard (com sublinha opcional, ex. "qtd + saldo"), KpiRow (grid responsivo)
│   ├── charts/              # HBarChart, PieChartCard, BarChartCard, StackedBarChartCard (Recharts) —
│   │                         # os três primeiros aceitam `corPorRotulo` opcional para cor fixa por rótulo
│   │                         # (ex. cor de status/categoria), em vez de ciclar a paleta padrão
│   ├── data-table/           # ResponsiveTable — tabela ordenável no desktop, cards empilhados no mobile;
│   │                         # suporta destaque de linha por item (EstiloLinha — cor de texto/negrito/fundo)
│   └── export/                # ExportExcelButton — link para um endpoint /*/export do backend
└── features/            # um diretório por relatório, só com o que é específico dele
    ├── faturamento/       # completo (piloto da migração) — Page, hook de dados, kpis.ts, charts.ts, api.ts
    ├── estoque/            # completo — mesmo padrão do piloto
    ├── cargas/              # completo — inclui destacarLinha (data > 3 dias vira vermelho/negrito)
    └── financeiro/          # completo — o mais complexo: KPIs com exclusão de recuperação judicial
                              # (kpis.ts), 4 gráficos principais (charts.ts) + 4 abas de resumo com
                              # tabela+gráfico (resumos.ts: categoria/filial/evolução mensal/total por dia),
                              # destaque de linha por status, e categorização de despesas (categorizacao.ts,
                              # a partir de categorias.json — cópia estática duplicada com
                              # app/excel/data/categorias_financeiro.json no backend; ver nota de risco de
                              # divergência em ambos os arquivos e no README.md da raiz)
```

Padrão-chave: tudo em `components/` é genérico (recebe dados/config via props) e não conhece nenhum relatório específico — cada `features/<relatorio>/` só fornece os dados e a configuração (colunas da tabela, séries dos gráficos, fórmulas de KPI). Os quatro relatórios já seguem esse padrão; ao portar um relatório novo no futuro, o trabalho é escrever um `features/<relatorio>/` seguindo o mesmo modelo, não criar componentes de UI do zero.
