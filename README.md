# RestDataAPI

API REST construída com **FastAPI** que serve como camada de **leitura de dados** entre um banco **SQL Server** e aplicações clientes. Expõe endpoints somente leitura (`GET`) com autenticação por API Key ou login Google Workspace, paginação, filtros e ordenação.

## Somente leitura (SELECT) — por design

Esta API **nunca executa `INSERT`, `UPDATE` ou `DELETE`**. Isso é garantido em três camadas independentes:

1. **Nenhuma rota de escrita existe.** Os routers só definem operações `GET`. Uma tentativa de `POST`/`PUT`/`DELETE` em qualquer rota retorna `405 Method Not Allowed`.
2. **Bloqueio em nível de ORM.** A sessão SQLAlchemy usada pela API (`app/database.py`) tem um listener `before_flush` que levanta `PermissionError` caso qualquer objeto novo, modificado ou removido esteja pendente — uma proteção extra caso algum código futuro tente gravar por engano.
3. **Recomendação de permissão no banco (mais importante):** configure o login do SQL Server usado pela API com permissão **somente `db_datareader`** (ou `GRANT SELECT` nas tabelas específicas), sem `db_datawriter`/`INSERT`/`UPDATE`/`DELETE`. Essa é a garantia mais forte, pois vale mesmo se o código da aplicação for alterado.

> Migrations (Alembic) continuam existindo, mas são uma ferramenta de administração de schema executada manualmente por um operador — não fazem parte da API que atende requisições dos clientes.

## Arquitetura

```
app/
├── main.py           # aplicação FastAPI, middlewares, rotas de health-check
├── config.py         # configurações via variáveis de ambiente (.env)
├── database.py        # engine SQLAlchemy e sessão de banco
├── security.py         # verificação de API Key e/ou sessão de login Google
├── auth_google.py      # verificação do ID token do Google e checagem de domínio
├── session.py           # emissão/verificação do JWT de sessão (cookie da SPA)
├── rate_limit.py        # instância do slowapi Limiter, compartilhada entre main.py e routers
├── models/            # modelos SQLAlchemy (tabelas)
├── schemas/            # modelos Pydantic (validação de entrada/saída)
├── crud/base.py        # operações de leitura (get/list) reutilizadas pelas rotas
└── routers/            # endpoints REST (GET) por entidade
alembic/                 # migrations do banco de dados
tests/                   # testes automatizados (pytest + SQLite em memória)
frontend/                # SPA web (React+Vite+TS) — ver "Frontend (SPA)" abaixo e frontend/README.md
client/                  # clients desktop (Tkinter) — ver "Clients desktop" abaixo
```

### Tabelas externas (não gerenciadas por este projeto)

Atualmente a API só lê tabelas que já existem em outro sistema (o Protheus). **Este projeto nunca cria, altera ou apaga essas tabelas** — quem é dono do schema é o Protheus:

- **TituloPagar** (tabela `SE2070` — Contas a Pagar): `rec_no (R_E_C_N_O_), filial, prefixo, numero, parcela, tipo, fornecedor, loja, emissao, vencimento_original, vencimento, valor, saldo, moeda, historico, data_baixa`.
  - Datas (`emissao`, `vencimento`, `vencimento_original`, `data_baixa`) são strings `AAAAMMDD`, o formato usado pelo dicionário de dados do Protheus — não são colunas `DATE`.
- **Fornecedor** (tabela `SA2070` — Fornecedores): `rec_no (R_E_C_N_O_), filial, codigo, loja, nome, nome_reduzido, cnpj_cpf, inscricao_estadual, endereco, bairro, municipio, estado, cep, ddd, telefone, contato, tipo, bloqueado`.
- **SaldoEstoque** (tabela `SB2070` — Saldo Atual de Estoque): `rec_no (R_E_C_N_O_), filial, codigo_produto, local, saldo_atual, quantidade_empenhada, quantidade_reservada, quantidade_pedido_venda, quantidade_pedido_compra, custo_medio, valor_atual`.
- **Produto** (tabela `SB1000` — Cadastro de Produtos): `rec_no (R_E_C_N_O_), filial, codigo, descricao, tipo, unidade_medida, grupo, local_padrao, conversao, ncm, peso_liquido, peso_bruto, codigo_barras, preco_venda, bloqueado`. Usada também como apoio (join) no relatório `/saldos-estoque/`.
- **TipoOperacao** (tabela `PA6000` — Tipos de Operação Financeira): `rec_no (R_E_C_N_O_), filial, codigo, descricao`. Usada apenas como apoio (join) no relatório `/financeiro/`, sem rota própria.
- **ItemCarga** (tabela `DAI070` — Itens de Carga): `rec_no (R_E_C_N_O_), filial, codigo, sequencia_carga, sequencia, data, pedido, cliente, loja, peso, nota_fiscal, serie`. Tabela principal do relatório `/cargas/`.
- **VeiculoCarga** (tabela `DAK070` — Veículos da Carga): `rec_no (R_E_C_N_O_), filial, codigo, sequencia_carga, data, caminhao, status, motorista`. Usada apenas como apoio (join) no relatório `/cargas/`, sem rota própria. `status` (`DAK_ACECAR`) é uma customização desta instalação — veja `/cargas/` abaixo. `motorista` (`DAK_MOTORI`) é usado só internamente, para o join com `DA4070`. `data` (`DAK_DATA`) é usado só internamente, para os filtros `data_inicial`/`data_final` de `/cargas/` (não confundir com `data` de `ItemCarga`, retornada em cada item).
- **Cliente** (tabela `SA1070` — Clientes): `rec_no (R_E_C_N_O_), filial, codigo, loja, nome, bairro, municipio`. Usada apenas como apoio (join) no relatório `/cargas/`, sem rota própria.
- **NotaFiscalSaida** (tabela `SE1070` — Notas Fiscais de Saída): `rec_no (R_E_C_N_O_), filial, prefixo, numero, cliente, loja, valor, carga, sequencia_carga`. Usada apenas como apoio (subconsulta correlacionada) no relatório `/cargas/`, para obter o valor da carga, sem rota própria.
- **Motorista** (tabela `DA4070` — Motoristas): `rec_no (R_E_C_N_O_), filial, codigo, nome`. Usada apenas como apoio (join opcional/`LEFT JOIN`) no relatório `/cargas/`, para obter o nome do motorista (`DAK_MOTORI`) do veículo, sem rota própria.
- **ItemFaturamento** (tabela `SD2070` — Notas Fiscais de Saída, Itens): `rec_no (R_E_C_N_O_), filial, emissao, codigo_produto, operacao, quantidade, total, custo`. Tabela principal do relatório `/faturamento/`. Não confundir com **NotaFiscalSaida** (`SE1070`), tabela diferente usada só no relatório de cargas. `operacao` (`D2_YOPER`) é uma customização desta instalação — veja `/faturamento/` abaixo.
  - `emissao` é string `AAAAMMDD`, como as demais datas do Protheus expostas por esta API.

Para todas:
- Registros com `D_E_L_E_T_ = '*'` (exclusão lógica do Protheus) são sempre filtrados pela API, tanto na listagem quanto na busca por id.
- Estão na lista `TABELAS_EXTERNAS` em `alembic/env.py`, que impede o Alembic (mesmo em `--autogenerate`) de gerar `CREATE`/`ALTER`/`DROP` para elas.

> `alembic/versions/` está vazio no momento: este projeto não possui, hoje, nenhuma tabela própria. A infraestrutura de migrations continua pronta para quando isso mudar (veja "Adicionando uma nova entidade/tabela" abaixo).

## Requisitos

- Python 3.11+
- Driver ODBC do SQL Server instalado no sistema (`ODBC Driver 18 for SQL Server`)
  - Ubuntu/Debian: siga o guia da Microsoft para instalar `msodbcsql18` e `unixodbc-dev`
  - Ou use Docker (veja abaixo), que já traz o driver instalado na imagem

## Configuração

1. Copie o arquivo de exemplo de variáveis de ambiente:
   ```bash
   cp .env.example .env
   ```
2. Edite `.env` com os dados de conexão do seu SQL Server e defina uma `API_KEY` forte.

## Instalação e execução local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# aplica as migrations no banco configurado no .env
alembic upgrade head

# inicia a API em modo desenvolvimento
uvicorn app.main:app --reload
```

A API estará disponível em `http://localhost:8000`, com documentação interativa em `http://localhost:8000/docs` (Swagger) e `http://localhost:8000/redoc`.

## Frontend (SPA)

Além dos clients desktop (`client/`), o diretório `frontend/` traz uma SPA web (React + Vite + TypeScript + Mantine) que consome esta mesma API, autenticando via login Google Workspace em vez de API Key (ver "Login via Google Workspace (SPA)" abaixo). Documentação completa de desenvolvimento em `frontend/README.md`.

Em produção, a SPA é servida pelo próprio FastAPI (mesma origem — `app.mount`/catch-all em `app/main.py`, ativo só quando `frontend/dist/` existe, gerado por `npm run build`); sem esse build, `/` continua sendo apenas o health-check JSON de sempre. Em desenvolvimento, rode a API (`uvicorn app.main:app --reload`) e o dev server da SPA (`cd frontend && npm run dev`) em paralelo — o Vite faz proxy das chamadas de API para a porta da API (ver `frontend/vite.config.ts`).

Os quatro relatórios estão completos: **Faturamento** (piloto da migração), **Estoque**, **Cargas** e **Financeiro** (o mais complexo — KPIs com exclusão de recuperação judicial, 4 gráficos principais + 4 abas de resumo com tabela+gráfico, destaque de linha por status e categorização de despesas), todos reaproveitando os mesmos componentes genéricos (`frontend/src/components/`).

## Executando com Docker

O `docker-compose.yml` sobe a API (que já inclui o build da SPA — o `Dockerfile` tem um estágio Node que builda `frontend/` antes da imagem final da API) e um SQL Server local para testes:

```bash
docker compose up --build
```

Depois de o container `db` subir, rode as migrations dentro do container da API:

```bash
docker compose exec api alembic upgrade head
```

## Autenticação

Todas as rotas de dados exigem o header `X-API-Key` (nome configurável via `API_KEY_NAME`) com o valor definido em `API_KEY` no `.env`. A comparação é feita em tempo constante (`secrets.compare_digest`) para não vazar informação por diferença de tempo de resposta.

```bash
curl -H "X-API-Key: SEU_VALOR_DE_API_KEY" http://localhost:8000/fornecedores/
```

Opcionalmente, é possível cadastrar **múltiplas chaves nomeadas** (uma por cliente/integração) via `API_KEYS` no `.env`, no formato `cliente1:chave1,cliente2:chave2` — isso permite revogar o acesso de um cliente específico sem invalidar os demais. Quando `API_KEYS` não é definido, a API cai no `API_KEY` único (retrocompatibilidade).

### Login via Google Workspace (SPA)

Além da API Key (usada pelos clients desktop em `client/`), as rotas de dados também aceitam uma **sessão de login via Google** — mecanismo pensado para uma futura SPA web, que não tem como armazenar uma API key com segurança num navegador. Os dois mecanismos coexistem: cada requisição é aceita se tiver **ou** um `X-API-Key` válido **ou** um cookie de sessão válido; nenhum dos dois é exigido junto com o outro, e a API Key continua funcionando exatamente como hoje.

Fluxo (Google Identity Services, ID token — não o Authorization Code flow completo, já que só precisamos de identidade, não de acesso contínuo a outras APIs do Google):

1. O frontend obtém um **ID token** assinado pelo Google (via `google.accounts.id`, com o `GOOGLE_CLIENT_ID` da aplicação) e envia para `POST /auth/google` como `{"credential": "<id_token>"}`.
2. O backend verifica o token (assinatura, `aud`, `exp`) com a lib `google-auth` — nunca confia em nada vindo do client sem essa verificação — e confere se o **domínio do e-mail** está na allowlist `ALLOWED_GOOGLE_DOMAINS` (`ALLOWED_GOOGLE_DOMAINS` vazio nega todo login, por design — falha fechado).
3. Se autorizado, o backend emite seu **próprio JWT de sessão** (não repassa o token do Google, que expira em ~1h) assinado com `SESSION_SECRET`, num cookie `httpOnly`+`Secure`+`SameSite=Lax`, válido por `SESSION_TTL_MINUTES` (padrão 8h).
4. `GET /auth/me` retorna o usuário da sessão atual; `POST /auth/logout` limpa o cookie.

> **Trade-off aceito**: a sessão é *stateless* (não há tabela de sessões) — uma sessão já emitida não pode ser revogada antes de expirar (ex.: um desligamento não derruba na hora uma sessão já aberta, só bloqueia logins futuros). Optamos por isso para não introduzir a primeira tabela própria da aplicação (hoje só existem entidades do Protheus, somente leitura por design) em troca de um TTL curto (8h).

## Segurança para exposição externa

- **Rate limiting**: todas as rotas têm um limite de requisições por IP (`RATE_LIMIT_DEFAULT` no `.env`, padrão `100/minute`), mitigando brute-force de API key e abuso acidental. `POST /auth/google` tem um limite adicional mais restrito (`10/minute`), por ser o endpoint de entrada do login.
- **Docs desabilitáveis**: `/docs`, `/redoc` e `/openapi.json` ficam públicos por padrão (sem exigir API Key) para facilitar o desenvolvimento local. Em qualquer ambiente exposto fora da rede interna, defina `DOCS_ENABLED=false` no `.env`.
- **CORS**: restrito por padrão (`FRONTEND_ORIGIN` vazio = nenhuma origem cross-site liberada) — necessário porque o cookie de sessão exige `allow_credentials=True`, incompatível com `allow_origins=["*"]` nos navegadores. Só defina `FRONTEND_ORIGIN` se a SPA for hospedada numa origem diferente da API; se ela for servida pelo próprio FastAPI (mesma origem), não é necessário.
- Estas proteções não substituem TLS: se a API for acessada fora de uma rede/VPN confiável, coloque-a atrás de um reverse proxy com HTTPS, já que a API Key trafega em texto claro no header, e o cookie `Secure` exige HTTPS para ser enviado pelo navegador.

## Endpoints principais

Todos os endpoints são `GET` — não existem rotas `POST`, `PUT` ou `DELETE`.

| Método | Rota                              | Descrição                          |
|--------|------------------------------------|-------------------------------------|
| GET    | `/titulos-pagar/`                  | Lista títulos a pagar (SE2070, filtra por filial/fornecedor/prefixo/numero) |
| GET    | `/titulos-pagar/{rec_no}`          | Obtém um título a pagar pelo `R_E_C_N_O_` |
| GET    | `/fornecedores/`                   | Lista fornecedores (SA2070, filtra por filial/codigo/cnpj_cpf/nome) |
| GET    | `/fornecedores/{rec_no}`           | Obtém um fornecedor pelo `R_E_C_N_O_` |
| GET    | `/produtos/`                       | Lista produtos (SB1000, filtra por filial/codigo/grupo) |
| GET    | `/produtos/{rec_no}`               | Obtém um produto pelo `R_E_C_N_O_` |
| GET    | `/financeiro/`                     | Relatório financeiro (réplica de `select_financeiro.sql`): títulos a pagar (SE2070) com fornecedor (SA2070) e descrição do tipo de operação (PA6000); filtra por `vencimento_de`/`vencimento_ate` |
| GET    | `/financeiro/export`               | Mesmo relatório acima, sem paginação, como planilha `.xlsx` (8 abas); filtra por `vencimento_de`/`vencimento_ate`/`status`/`filial`/`fornecedor`/`tipo`/`tipo_operacao`/`categoria` |
| GET    | `/saldos-estoque/`                 | Relatório de saldo de estoque (baseado em `select_estoque_produtos.sql`): saldos (SB2070) com descrição e fator de conversão do produto (SB1000); filtra por `tipo_produto`/`local` |
| GET    | `/saldos-estoque/export`           | Mesmo relatório acima, sem paginação, como planilha `.xlsx` (4 abas); filtra por `tipo_produto`/`local`/`filial`/`codigo`/`descricao` |
| GET    | `/cargas/`                         | Relatório de cargas (baseado em `select_cargas.sql`): itens de carga (DAI070) com veículo (DAK070), cliente (SA1070, com bairro/município) e valor da nota fiscal (SE1070) e, opcionalmente, motorista (DA4070); filtra por `data_inicial`/`data_final`/`status` |
| GET    | `/cargas/export`                   | Mesmo relatório acima, sem paginação, como planilha `.xlsx` (4 abas); filtra por `data_inicial`/`data_final`/`status`/`filial`/`cliente`/`caminhao` |
| GET    | `/faturamento/`                    | Relatório de faturamento (baseado em `select_faturamento.sql`): notas fiscais de saída (SD2070) de produtos acabados (SB1000, `B1_TIPO='PA'`), agregadas por filial/dia do mês/produto; filtra por `data_inicial`/`data_final` |
| GET    | `/faturamento/export`              | Mesmo relatório acima, sem paginação, como planilha `.xlsx` (4 abas); filtra por `data_inicial`/`data_final`/`filial`/`produto` |

Parâmetros comuns de listagem: `skip`, `limit` (paginação), `order_by` (ex.: `nome` ou `-criado_em` para ordem decrescente) e filtros por campo (ex.: `?filial=01`).

A resposta paginada (`{"skip", "limit", "items"}`) não inclui um total de registros. Um `count(*)` exato sobre os mesmos `JOIN`s/filtros da listagem não consegue parar cedo como o `SELECT` paginado (que usa `ORDER BY` + `OFFSET`/`FETCH` e para assim que preenche a página) — precisa avaliar todas as linhas que casam nos joins até o fim. Em tabelas grandes do Protheus isso chegou a levar o `count()` sozinho a mais de 45s mesmo com a página respondendo em ~1s, por isso foi removido. Para consumir o relatório inteiro, pagine em loop incrementando `skip` até receber uma página com `items` vazio (é o que `client/api_client.py` já faz).

### `/financeiro/`

Baseado no `SELECT` de `select_financeiro.sql`: junta `SE2070` (títulos a pagar) com `SA2070` (fornecedor, join obrigatório — títulos sem fornecedor cadastrado na filial `"  "` não aparecem) e `PA6000` (tipo de operação, join opcional — `descricao_operacao` vem `null` quando não há correspondência). Aplica como regra de negócio fixa (sempre ativa):

- Apenas títulos não excluídos (`D_E_L_E_T_ != '*'`);
- `tipo` fora de `PA`, `PR`, `NDF`.

Diferente da consulta original — que fixa o vencimento mínimo em `'20260301'` —, aqui o período **não é fixo**: é parametrizável via query string.

- `vencimento_de` (opcional): filtra pelo vencimento real (`E2_VENCREA`, formato `AAAAMMDD`), trazendo apenas títulos com `vencimento_real >= vencimento_de`. Sem o parâmetro, assume a data atual do sistema (equivalente a `vencimento_de=<hoje>`).
- `vencimento_ate` (opcional): filtra por `vencimento_real <= vencimento_ate`. Sem o parâmetro, não limita o vencimento máximo.
- `status` (opcional): filtra pelo mesmo status já calculado nos clients desktop, com base em `E2_BAIXA`/`E2_VENCREA` — `em_aberto` (sem data de baixa e `vencimento_real >= hoje`), `vencido` (sem data de baixa e `vencimento_real < hoje`) ou `baixado` (com data de baixa preenchida). Sem o parâmetro, não filtra por status. Como `vencimento_de` já começa em hoje por padrão, para ver títulos `vencido` é preciso recuar `vencimento_de`.

Suporta apenas paginação (`skip`, `limit`) e os filtros acima — não tem rota de detalhe por id, pois o `SELECT` original não expõe um identificador único de linha.

`GET /financeiro/export` gera a planilha `.xlsx` do período inteiro (sem paginação — réplica do client desktop), com as mesmas 8 abas de `client/app_financeiro.py` (Financeiro, Resumo, Por Fornecedor, Por Tipo de Operação, Resumo por Categoria, Evolução Mensal, Total por Dia, Resumo por Filial), geradas em `app/excel/financeiro.py`. Aceita `vencimento_de`/`vencimento_ate`/`status` (iguais ao endpoint de listagem) e também `filial`/`fornecedor`/`tipo`/`tipo_operacao`/`categoria` — únicos aqui, aplicados em Python após a consulta, só para a exportação bater com o que a SPA mostra filtrado na tela.

A coluna `categoria` (classificação da despesa — ex. "T.I.", "Combustível", "Jurídico") não vem do Protheus: é calculada por regras de correspondência de texto contra fornecedor/histórico, réplica de `client/categorias.py`. As regras (extraídas de `client/categorias.xlsx`) estão duplicadas como JSON estático em dois lugares — `app/excel/data/categorias_financeiro.json` (usado só na exportação Excel) e `frontend/src/features/financeiro/categorias.json` (usado na tela da SPA) — sem nenhum mecanismo que os mantenha sincronizados; editar `categorias.xlsx` não propaga automaticamente para nenhum dos dois.

O client desktop deste endpoint é `client/app_financeiro.py` (veja "Clients desktop" abaixo); a SPA (`frontend/`) também já implementa este relatório por completo (ver "Frontend (SPA)" acima).

### `/saldos-estoque/`

Baseado no `SELECT` de `select_estoque_produtos.sql`: junta `SB2070` (saldo de estoque) com `SB1000` (produto, join obrigatório na filial `"  "` — saldos de produtos sem cadastro correspondente não aparecem). Aplica como regra de negócio fixa (sempre ativa):

- Apenas saldos não excluídos (`D_E_L_E_T_ != '*'`);
- `saldo_atual > 0`.

Diferente de `/financeiro/`, o tipo de produto e o armazém **não são fixos** — são parametrizáveis via query string, para que cada cliente escolha o recorte de estoque que quer analisar:

- `tipo_produto` (opcional): filtra pelo tipo do produto (`B1_TIPO`), ex. `PA` (produto acabado) ou `AM` (vasilhame). Sem o parâmetro, traz qualquer tipo.
- `local` (opcional): filtra pelo armazém (`B2_LOCAL`), ex. `01` ou `20`. Sem o parâmetro, traz qualquer armazém.

O campo `quantidade` replica `B2_QATU / B1_CONV` da consulta original (quantidade convertida pela unidade de medida do produto). Suporta paginação (`skip`, `limit`) e os dois filtros acima — não tem rota de detalhe por id, pois o `SELECT` original não expõe um identificador único de linha.

`GET /saldos-estoque/export` gera a planilha `.xlsx` do recorte inteiro (sem paginação — réplica do client desktop), com as mesmas 4 abas de `client/app_estoque.py` (Estoque, Resumo, Por Filial, Top Produtos), geradas em `app/excel/estoque.py`. Aceita `tipo_produto`/`local` (iguais ao endpoint de listagem) e também `filial`/`codigo`/`descricao` — únicos aqui, aplicados em Python após a consulta, só para a exportação bater com o que a SPA mostra filtrado na tela.

O client desktop deste endpoint é `client/app_estoque.py` (veja "Clients desktop" abaixo); a SPA (`frontend/`) também já implementa este relatório por completo (ver "Frontend (SPA)" acima).

### `/cargas/`

Baseado no `SELECT` de `select_cargas.sql`: junta `DAI070` (item de carga) com `DAK070` (veículo, join obrigatório por filial/código/sequência de carga) e `SA1070` (cliente, join obrigatório por filial/código/loja — itens sem cliente cadastrado não aparecem; também traz bairro/município do cliente). `DA4070` (motorista) é `LEFT JOIN` — join opcional por filial/código via `DAK_MOTORI`: veículo sem motorista cadastrado continua aparecendo, só com `motorista` nulo. `DA5070` (percurso) não faz mais parte desta consulta (removida em uma versão anterior de `select_cargas.sql` — nem o join nem uma descrição de percurso são expostos). O valor da carga vem de uma subconsulta correlacionada em `SE1070` (nota fiscal de saída, casando filial/série/número/cliente/loja — `0` quando não há nota fiscal correspondente, equivalente ao `ISNULL(...,0)` da consulta original), não de `DAK070`. Diferente da consulta original, essa subconsulta também restringe parcela (`E1_PARCELA = '  '`) e tipo (`E1_TIPO = 'NF '`) e casa pela carga/sequência de carga (`E1_YCARGA`/`E1_YSEQCAR`, campos customizados desta instalação do Protheus) — dá mais assertividade ao valor retornado, evitando pegar por engano uma nota de outra parcela/tipo ou de outra carga que coincida em filial/série/número/cliente/loja. Já testamos substituir essa subconsulta por um LEFT JOIN único (esperando ganho de performance em relatórios de vários dias), mas a mudança piorou o tempo de resposta real no SQL Server — mantida a subconsulta correlacionada original. Aplica como regra de negócio fixa (sempre ativa):

- Apenas itens não excluídos (`D_E_L_E_T_ != '*'`);
- Sequência de item diferente de `999999` (convenção do Protheus para item cancelado).

Diferente da consulta original — que fixa a data mínima em `'20260801'` e o status em `:STATUS_CARGA` — aqui os dois **não são fixos**: são parametrizáveis via query string.

- `data_inicial` (opcional): filtra pela data do veículo (`DAK_DATA` em `DAK070`, formato `AAAAMMDD`), trazendo apenas cargas com `data >= data_inicial`. Sem o parâmetro, assume a data atual do sistema (equivalente a `data_inicial=<hoje>`). Filtra em `DAK070`, não em `DAI070` (que também tem uma data, `DAI_DATA`, retornada no campo `data` de cada item): `DAK070` tem uma linha por veículo/sequência de carga, bem menos linhas que `DAI070` (uma por item) — filtrar na tabela menor é mais barato.
- `data_final` (opcional): mesma coluna (`DAK_DATA`), trazendo apenas cargas com `data <= data_final`. Sem o parâmetro, não há limite superior.
- `status` (opcional, valores `aberta`/`encerrada`): filtra pelo status da carga (`DAK_ACECAR`) — `encerrada` (códigos `7` ou `8`) ou `aberta` (qualquer outro código, incluindo nulo). Sem o parâmetro, traz cargas de qualquer status. `DAK_ACECAR` é uma customização desta instalação do Protheus (no dicionário padrão é "Acerto de Carga Ok?", campo `C(1)` sem lista pública de valores) — os códigos `7`/`8` foram confirmados pelo usuário, não por documentação oficial. O filtro é resolvido no banco (`IN`/`NOT IN` com tratamento explícito de `NULL` — veja `_filtro_cargas` em `app/routers/cargas.py`), não no cliente, para não trafegar o volume completo do relatório a cada consulta. O nome do parâmetro (`encerrada`) é mantido por retrocompatibilidade — o texto de fato devolvido no campo `status_carga` (veja abaixo) é `"Fechada"`, igual ao `CASE` de `select_cargas.sql`.

Assim como `select_cargas.sql`, os campos `caminhao` e `status_carga` já vêm formatados pela própria consulta (via `CASE`/`case()` do SQLAlchemy, calculado no banco — sem custo adicional no plano de execução, pois não entra em `JOIN`/`WHERE`): `caminhao` substitui a placa `KHA0902` por `"Cliente"` (retirada pelo próprio cliente, sem caminhão terceirizado); `status_carga` já vem como `"Aberta"`/`"Fechada"` em vez do código bruto de `DAK_ACECAR`. O `CASE` de ambos tem `ELSE`, então nenhum dos dois é nulo. Isso evita que cada client desktop precise reclassificar essas colunas linha a linha depois de carregar os dados.

**Performance / paginação.** `/cargas/` usa uma única query (`_query_cargas` em `app/routers/cargas.py`) com `ORDER BY` + `OFFSET`/`FETCH` para paginar — igual aos demais relatórios. Já tentamos separar em duas consultas (uma rasa, só com `R_E_C_N_O_` — chave primária de `DAI070` —, para achar a página; outra com `WHERE R_E_C_N_O_ IN (...)` para buscar a projeção completa só dessas linhas), na expectativa de blindar a subquery de `SE1070`/os `LEFT JOIN` de apoio contra planos onde o banco os calcula para mais linhas do que a página. Na prática, medido contra o SQL Server real, essa estratégia foi **bem mais lenta** — provável indício de que `R_E_C_N_O_` não tem índice de suporte nesta instalação do Protheus, fazendo o `IN (...)` da segunda consulta exigir um scan em vez de um seek, além do custo de reabrir todos os joins do zero. Revertida para a query única; não tentar de novo sem antes confirmar (`sys.indexes` ou Execution Plan) que `R_E_C_N_O_` tem índice único em `DAI070`.

O gargalo real, se `/cargas/` estiver lento, tende a estar em falta de índice nas tabelas do Protheus (que esta API não gerencia — são de responsabilidade de quem administra o SQL Server), não na forma da query. Índices recomendados, mapeados às colunas usadas em `JOIN`/`WHERE`/`ORDER BY` desta consulta:

```sql
-- DAK070: filtro de data (DAK_DATA, mais seletivo aqui do que em DAI070 —
-- uma linha por veículo/sequência de carga, não por item) + flag de
-- exclusão. Colunas de join/status incluídas para cobrir a consulta.
CREATE INDEX IX_DAK070_Cargas ON DAK070 (D_E_L_E_T_, DAK_DATA) INCLUDE (DAK_FILIAL, DAK_COD, DAK_SEQCAR, DAK_ACECAR, DAK_CAMINH, DAK_MOTORI);

-- DAI070: sem filtro de data (migrou para DAK070); flag de exclusão +
-- sequência cancelada, e as colunas de join/ordenação/saída.
CREATE INDEX IX_DAI070_Cargas ON DAI070 (D_E_L_E_T_, DAI_SEQUEN) INCLUDE (DAI_FILIAL, DAI_COD, DAI_SEQCAR, DAI_DATA, DAI_CLIENT, DAI_LOJA, DAI_SERIE, DAI_NFISCA, DAI_PEDIDO, DAI_PESO);

-- SE1070: subquery correlacionada de valor (só roda para a página, mas se
-- beneficia de um seek em vez de scan por linha)
CREATE INDEX IX_SE1070_Cargas ON SE1070 (E1_FILIAL, E1_CLIENTE, E1_LOJA, E1_PREFIXO, E1_NUM) INCLUDE (D_E_L_E_T_, E1_PARCELA, E1_TIPO, E1_YCARGA, E1_YSEQCAR, E1_VALOR);
```

`SA1070` e `DA4070` são tabelas de cadastro (cliente/motorista) geralmente já indexadas por `FILIAL`+`COD` como chave; confirme com `SET STATISTICS IO/TIME` ou o "Actual Execution Plan" do SSMS antes/depois de aplicar, seguindo o mesmo método já usado para decidir a estratégia da subquery de `SE1070` (ver comentário em `_query_cargas`).

Suporta paginação (`skip`, `limit`) e os filtros acima — não tem rota de detalhe por id, pois o `SELECT` original não expõe um identificador único de linha.

`GET /cargas/export` gera a planilha `.xlsx` do período inteiro (sem paginação — réplica do client desktop), com as mesmas 4 abas de `client/app_cargas.py` (Cargas, Resumo, Por Filial, Top Clientes), geradas em `app/excel/cargas.py`. Aceita `data_inicial`/`data_final`/`status` (iguais ao endpoint de listagem) e também `filial`/`cliente`/`caminhao` — únicos aqui, aplicados em Python após a consulta, só para a exportação bater com o que a SPA mostra filtrado na tela. Uma "carga" é identificada por `(filial, codigo)` — cada linha da API é um **item** de uma carga (uma carga pode ter vários pedidos/itens), então "quantidade de cargas" nas abas Resumo/Por Filial conta pares `(filial, codigo)` distintos, não linhas.

O client desktop deste endpoint é `client/app_cargas.py` (veja "Clients desktop" abaixo); a SPA (`frontend/`) também já implementa este relatório por completo (ver "Frontend (SPA)" acima), incluindo o destaque visual de linhas com `data` a mais de 3 dias da data atual (réplica da tag `data_distante` do client desktop, generalizada em `ResponsiveTable`/`EstiloLinha` para outros relatórios reaproveitarem — ex. o destaque por status em Financeiro).

### `/faturamento/`

Baseado no `SELECT` de `select_faturamento.sql`. A subconsulta interna **não agrega nada** — é uma projeção linha a linha de `SD2070` (item de nota fiscal de saída), calculando por linha a quantidade (`QTDE`), o faturamento (`FATURAMENTO`, zerado para bonificação — veja abaixo) e o custo (`CUSTO`, `D2_CUSTO1` puro), sempre juntando com `SB1000` (produto, join obrigatório por filial/código — `B1_FILIAL = '  '`, `B1_TIPO = 'PA'`: só produtos acabados; item sem produto correspondente do tipo `PA` não aparece). É a consulta externa quem agrega tudo por **filial, dia do mês e produto**, somando `qtde`/`faturamento`/`custo` e só então derivando `preco_medio` e `lucro_bruto` a partir dessas somas (veja abaixo). Réplica exata dessa estrutura no SQLAlchemy (`app/routers/faturamento.py`) — uma única camada de agregação, diferente de versões anteriores deste endpoint, que replicavam uma agregação em duas camadas hoje removida da consulta original. Aplica como regra de negócio fixa (sempre ativa):

- Apenas itens não excluídos (`D_E_L_E_T_ != '*'`);
- Apenas produtos do tipo `PA` (produto acabado);
- Apenas os tipos de operação (`D2_YOPER`, customização desta instalação do Protheus) `501` (venda) e `542`/`543`/`544` (bonificação) — outros tipos são ignorados.

Para itens com `D2_YOPER = '542'/'543'/'544'` (bonificação), o `faturamento` entra como **zero** — dar um produto de bonificação não gera receita. `quantidade`, porém, conta normalmente (sempre `D2_QUANT/B1_CONV`, sem exceção) — uma bonificação aumenta a quantidade movimentada do produto sem aumentar o faturamento do grupo. `preco_medio` é `SUM(faturamento)/SUM(qtde)` — uma **média ponderada pela quantidade** (diferente de uma versão anterior, que fazia `AVG` de uma razão por linha, dando peso igual a cada nota independente da quantidade); `lucro_bruto` é `SUM(faturamento) - SUM(custo)`. Os dois usam o `faturamento` já zerado para bonificação, não o `D2_TOTAL` bruto, então um item de bonificação sempre reduz o preço médio ponderado do grupo e contribui com `lucro_bruto = -custo` (prejuízo igual ao custo do produto doado). `custo` (`SUM(D2_CUSTO1)`) também é exposto diretamente como campo próprio da resposta.

`margem` (`lucro_bruto / faturamento * 100`) e `markup` (`lucro_bruto / custo * 100`) são as duas leituras de rentabilidade do grupo — mesmo numerador (`lucro_bruto`), denominador diferente: `margem` nunca chega a 100% (é uma fração do faturamento), `markup` não tem teto (compara o lucro ao custo, podendo superar 100% quando o lucro é maior que o próprio custo). `markup` é campo novo nesta versão de `select_faturamento.sql`.

**`dia` é o dia do mês da emissão (`DAY(D2_EMISSAO)`, 1 a 31) — não uma data completa.** Se o período (`data_inicial`/`data_final`) atravessar mais de um mês, dias iguais de meses diferentes são somados no mesmo grupo (ex.: vendas do dia 5 de janeiro e do dia 5 de fevereiro aparecem juntas como um único "dia 5"). Comportamento herdado de `select_faturamento.sql`, não uma escolha desta API. `DAY(D2_EMISSAO)` é replicado com `CAST(SUBSTRING(D2_EMISSAO, 7, 2) AS INTEGER)` (`D2_EMISSAO` é string `AAAAMMDD`, não uma coluna `DATE`) — como a subconsulta interna não tem mais `GROUP BY`, essa expressão aparece uma única vez no SQL final, então `7`/`2` podem ser inteiros Python normais (versões anteriores deste endpoint precisavam de `literal_column` para forçá-los a compilar como texto SQL fixo, já que a mesma expressão aparecia duas vezes — uma na lista de colunas, outra no `GROUP BY` da camada interna que existia então — e o SQL Server exige texto byte-a-byte idêntico nas duas ocorrências para validar o `GROUP BY`; sem essa segunda ocorrência, o problema não existe mais).

- `data_inicial` (opcional): filtra pela emissão da nota (`D2_EMISSAO`, formato `AAAAMMDD`), trazendo apenas itens com `emissao >= data_inicial`. Sem o parâmetro, assume a data atual do sistema.
- `data_final` (opcional): filtra por `emissao <= data_final`. Sem o parâmetro, não há limite superior.

`margem`, `markup` e `preco_medio` podem vir **`null`** — quando o denominador da razão é zero para aquele grupo (ex.: um filial/dia/produto só com bonificação, sem nenhuma venda, tem `faturamento` total zero; `qtde`/`custo` zerados também são possíveis em tese). A consulta original (SQL Server) lançaria "Divide by zero error" nesse caso — risco que era só teórico até aparecer de fato num teste da SPA (piloto de Faturamento, Fase 3 do plano); corrigido envolvendo os denominadores em `NULLIF(x, 0)`, que faz SQL Server e SQLite concordarem (`NULL`, não erro). `null` aqui significa "não é possível calcular essa razão para este grupo", não "zero" — o client deve tratar como tal (ex.: exibir "—", não "0,0%").

Suporta paginação (`skip`, `limit`) e os dois filtros de data acima — não tem rota de detalhe por id, pois o `SELECT` original não expõe um identificador único de linha (o resultado já é agregado).

`GET /faturamento/export` gera a planilha `.xlsx` do período inteiro (sem paginação — réplica do client desktop, que carrega tudo antes de exportar), com as mesmas 4 abas de `client/app_faturamento.py` (Faturamento, Resumo, Por Filial, Top Produtos), geradas em `app/excel/faturamento.py` (sem depender de pandas, diferente dos clients desktop — agregações em Python puro). Aceita `data_inicial`/`data_final` (iguais ao endpoint de listagem) e também `filial`/`produto` — únicos aqui, não em `GET /faturamento/` — aplicados em Python após a consulta, só para a exportação bater com o que o usuário está vendo filtrado na tela da SPA (não são filtros de negócio da consulta).

O client desktop deste endpoint é `client/app_faturamento.py` (veja "Clients desktop" abaixo); a SPA (`frontend/`) também já implementa este relatório por completo — foi o piloto da migração (ver "Frontend (SPA)" acima).

## Clients desktop

Além da API, o diretório `client/` traz aplicações desktop (Tkinter) que consomem os relatórios via `APIClient` (`client/api_client.py`), com filtros, KPIs, gráficos e exportação para Excel. Os quatro exibem o logotipo (`client/logo.jpg`) no canto superior esquerdo da janela; se o arquivo não existir, o cabeçalho é exibido sem logotipo, sem interromper a aplicação:

| Script                     | Endpoint            | Observação |
|-----------------------------|---------------------|------------|
| `client/app_financeiro.py`  | `/financeiro/`      | `vencimento_de`/`vencimento_ate`/`status` já vão para a API (período inicia na data atual, mesmo padrão da API); demais filtros são aplicados no cliente. |
| `client/app_estoque.py`     | `/saldos-estoque/`  | `tipo_produto`/`local` resolvidos por um seletor de "Tipo de Estoque". |
| `client/app_cargas.py`      | `/cargas/`          | `data_inicial`/`data_final`/`status` já vão para a API (os dois seletores de data — "Data de"/"Data até" — já iniciam na data de hoje, igual ao padrão da API; Status tem só "Aberta"/"Fechada" no seletor, resolvido no banco por causa do volume do relatório); demais filtros (filial, cliente, caminhão) são aplicados no cliente. `caminhao` e `status_carga` já chegam formatados da API (placa `KHA0902` como "Cliente"; "Aberta"/"Fechada" em vez do código bruto) — o client não reclassifica essas colunas. `motorista` (join opcional) pode vir nulo; exibido como "—" na tabela, junto com bairro/município do cliente. |
| `client/app_faturamento.py` | `/faturamento/`     | Seletores de "Mês"/"Ano" (não "Data de"/"Data até") — a tela sempre consulta a API por um único mês por vez, calculando `data_inicial`/`data_final` como o primeiro e o último dia do mês escolhido, porque a API agrega por dia do mês (não por data completa) e misturaria dias iguais de meses diferentes se o período enviado cobrisse mais de um mês. Filtros de Filial e Produto (por código ou descrição) são aplicados no cliente. |

Para rodar:

```bash
cd client
cp .env.example .env   # ajuste API_BASE_URL/API_KEY
pip install -r requirements.txt
python app_cargas.py
```

## Testes

Os testes usam SQLite em memória (não requerem SQL Server nem driver ODBC instalado). Como a API não tem rotas de escrita, os dados de teste são inseridos diretamente via SQLAlchemy (fixture `db_session`), não via HTTP:

```bash
pytest
```

Inclui um teste dedicado (`tests/test_read_only_guard.py`) que valida a proteção de escrita em nível de ORM de forma isolada, e testes que confirmam que `POST`/`PUT`/`DELETE` retornam `405` em todas as entidades.

## Adicionando uma nova entidade/tabela

1. Crie o modelo SQLAlchemy em `app/models/` e registre-o em `app/models/__init__.py`.
2. Crie o schema Pydantic `Read` (somente leitura) em `app/schemas/`.
3. Crie o router em `app/routers/` reutilizando `CRUDBase.get`/`CRUDBase.list` (veja `app/routers/fornecedores.py` como referência) e registre-o em `app/main.py`. Não adicione rotas `POST`/`PUT`/`DELETE`.
4. **Se a tabela já existe em outro sistema** (ex.: um ERP) e este projeto não deve gerenciá-la: adicione o nome dela em `TABELAS_EXTERNAS` (`alembic/env.py`) para impedir que o Alembic gere DDL para ela, e implemente qualquer filtro obrigatório (ex.: exclusão lógica) sobrescrevendo `CRUDBase._base_query` — veja `app/routers/titulos_pagar.py`.
5. **Se a tabela é nova e deste projeto**, gere a migration: `alembic revision --autogenerate -m "adiciona tabela X"`, revise o arquivo gerado e rode `alembic upgrade head` — isso é administração de schema, feita fora da API.
