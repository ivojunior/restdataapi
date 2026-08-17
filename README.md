# RestDataAPI

API REST construída com **FastAPI** que serve como camada de **leitura de dados** entre um banco **SQL Server** e aplicações clientes. Expõe endpoints somente leitura (`GET`) com autenticação por API Key, paginação, filtros e ordenação.

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
├── security.py         # verificação de API Key
├── models/            # modelos SQLAlchemy (tabelas)
├── schemas/            # modelos Pydantic (validação de entrada/saída)
├── crud/base.py        # operações de leitura (get/list) reutilizadas pelas rotas
└── routers/            # endpoints REST (GET) por entidade
alembic/                 # migrations do banco de dados
tests/                   # testes automatizados (pytest + SQLite em memória)
```

### Tabelas externas (não gerenciadas por este projeto)

Atualmente a API só lê tabelas que já existem em outro sistema (o Protheus). **Este projeto nunca cria, altera ou apaga essas tabelas** — quem é dono do schema é o Protheus:

- **TituloPagar** (tabela `SE2070` — Contas a Pagar): `rec_no (R_E_C_N_O_), filial, prefixo, numero, parcela, tipo, fornecedor, loja, emissao, vencimento_original, vencimento, valor, saldo, moeda, historico, data_baixa`.
  - Datas (`emissao`, `vencimento`, `vencimento_original`, `data_baixa`) são strings `AAAAMMDD`, o formato usado pelo dicionário de dados do Protheus — não são colunas `DATE`.
- **Fornecedor** (tabela `SA2070` — Fornecedores): `rec_no (R_E_C_N_O_), filial, codigo, loja, nome, nome_reduzido, cnpj_cpf, inscricao_estadual, endereco, bairro, municipio, estado, cep, ddd, telefone, contato, tipo, bloqueado`.
- **SaldoEstoque** (tabela `SB2070` — Saldo Atual de Estoque): `rec_no (R_E_C_N_O_), filial, codigo_produto, local, saldo_atual, quantidade_empenhada, quantidade_reservada, quantidade_pedido_venda, quantidade_pedido_compra, custo_medio`.
- **Produto** (tabela `SB1000` — Cadastro de Produtos): `rec_no (R_E_C_N_O_), filial, codigo, descricao, tipo, unidade_medida, grupo, local_padrao, ncm, peso_liquido, peso_bruto, codigo_barras, preco_venda, bloqueado`.

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

## Executando com Docker

O `docker-compose.yml` sobe a API e um SQL Server local para testes:

```bash
docker compose up --build
```

Depois de o container `db` subir, rode as migrations dentro do container da API:

```bash
docker compose exec api alembic upgrade head
```

## Autenticação

Todas as rotas de dados exigem o header `X-API-Key` (nome configurável via `API_KEY_NAME`) com o valor definido em `API_KEY` no `.env`.

```bash
curl -H "X-API-Key: SEU_VALOR_DE_API_KEY" http://localhost:8000/fornecedores/
```

## Endpoints principais

Todos os endpoints são `GET` — não existem rotas `POST`, `PUT` ou `DELETE`.

| Método | Rota                              | Descrição                          |
|--------|------------------------------------|-------------------------------------|
| GET    | `/titulos-pagar/`                  | Lista títulos a pagar (SE2070, filtra por filial/fornecedor/prefixo/numero) |
| GET    | `/titulos-pagar/{rec_no}`          | Obtém um título a pagar pelo `R_E_C_N_O_` |
| GET    | `/fornecedores/`                   | Lista fornecedores (SA2070, filtra por filial/codigo/cnpj_cpf/nome) |
| GET    | `/fornecedores/{rec_no}`           | Obtém um fornecedor pelo `R_E_C_N_O_` |
| GET    | `/saldos-estoque/`                 | Lista saldos de estoque (SB2070, filtra por filial/codigo_produto/local) |
| GET    | `/saldos-estoque/{rec_no}`         | Obtém um saldo de estoque pelo `R_E_C_N_O_` |
| GET    | `/produtos/`                       | Lista produtos (SB1000, filtra por filial/codigo/grupo) |
| GET    | `/produtos/{rec_no}`               | Obtém um produto pelo `R_E_C_N_O_` |

Parâmetros comuns de listagem: `skip`, `limit` (paginação), `order_by` (ex.: `nome` ou `-criado_em` para ordem decrescente) e filtros por campo (ex.: `?filial=01`).

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
