import { Alert, Button, Group, Loader, Paper, Select, SimpleGrid, Stack, Tabs, Text, TextInput, Title } from '@mantine/core'
import { IconAlertCircle, IconRefresh } from '@tabler/icons-react'
import { useMemo, useState } from 'react'
import { BarChartCard } from '../../components/charts/BarChartCard'
import { HBarChart } from '../../components/charts/HBarChart'
import { PieChartCard } from '../../components/charts/PieChartCard'
import { StackedBarChartCard } from '../../components/charts/StackedBarChartCard'
import { ResponsiveTable, type ColunaTabela, type EstiloLinha } from '../../components/data-table/ResponsiveTable'
import { ExportExcelButton } from '../../components/export/ExportExcelButton'
import { KpiCard } from '../../components/kpi/KpiCard'
import { KpiRow } from '../../components/kpi/KpiRow'
import { hojeAAAAMMDD } from '../../utils/date'
import { formatarBRL, formatarDataBR, formatarPct, ouTraco } from '../../utils/format'
import { urlExportacao } from './api'
import { corDaCategoria } from './categoriaCores'
import { CATEGORIAS_CANONICAS, NAO_CLASSIFICADO } from './categorizacao'
import { corSaldoPorMes, distribuicaoPorStatus, saldoPorMesVencimento, saldoPorTipoOperacao, topFornecedoresPorSaldo } from './charts'
import { calcularKpis } from './kpis'
import { PeriodoStatusToggle } from './PeriodoStatusToggle'
import { resumoEvolucaoMensal, resumoPorCategoria, resumoPorFilial, resumoTotalPorDia } from './resumos'
import { STATUS_CORES, type FinanceiroItemEnriquecido } from './types'
import { useFinanceiroData } from './useFinanceiroData'

const CATEGORIA_OPCOES = [
  { value: '', label: '(Todas)' },
  ...CATEGORIAS_CANONICAS.map((c) => ({ value: c, label: c })),
  { value: NAO_CLASSIFICADO, label: NAO_CLASSIFICADO },
]

// Fundo claro de cada status na tabela "Dados" — réplica de
// `_tree.tag_configure(status, background=...)` em client/app_financeiro.py
// (mais claro que STATUS_CORES, que é usado nos gráficos/KPIs).
const STATUS_FUNDO: Record<string, string> = {
  'Em aberto': '#eafaf1',
  Vencido: '#fdecea',
  Baixado: '#f2f3f4',
}

function destacarLinha(item: FinanceiroItemEnriquecido): EstiloLinha {
  return { corFundo: STATUS_FUNDO[item.status] }
}

const COLUNAS: ColunaTabela<FinanceiroItemEnriquecido>[] = [
  { chave: 'filial', titulo: 'Filial' },
  { chave: 'numero', titulo: 'Número' },
  { chave: 'parcela', titulo: 'Parcela' },
  { chave: 'tipo', titulo: 'Tipo' },
  { chave: 'codigo_operacao', titulo: 'Cód. Op.', formatar: (i) => ouTraco(i.codigo_operacao) },
  { chave: 'descricao_operacao', titulo: 'Tipo Operação', formatar: (i) => ouTraco(i.descricao_operacao) },
  { chave: 'nome_fornecedor', titulo: 'Fornecedor', formatar: (i) => ouTraco(i.nome_fornecedor) },
  { chave: 'categoria', titulo: 'Categoria' },
  { chave: 'emissao', titulo: 'Emissão', align: 'center', formatar: (i) => formatarDataBR(i.emissao) },
  { chave: 'vencimento_real', titulo: 'Vencimento', align: 'center', formatar: (i) => formatarDataBR(i.vencimento_real) },
  { chave: 'valor', titulo: 'Valor (R$)', align: 'right', formatar: (i) => formatarBRL(Number(i.valor)) },
  { chave: 'saldo', titulo: 'Saldo (R$)', align: 'right', formatar: (i) => formatarBRL(Number(i.saldo)) },
  { chave: 'historico', titulo: 'Histórico' },
  {
    chave: 'recuperacao_judicial', titulo: 'Rec. Judicial', align: 'center',
    formatar: (i) => ((i.recuperacao_judicial ?? '').trim() === '1' ? 'Sim' : 'Não'),
  },
  { chave: 'status', titulo: 'Status', align: 'center' },
]

const COLUNAS_CATEGORIA: ColunaTabela<{ categoria: string; qtd: number; valorTotal: number; pct: number; valorMedio: number }>[] = [
  { chave: 'categoria', titulo: 'Categoria' },
  { chave: 'qtd', titulo: 'Qtd', align: 'right', formatar: (i) => i.qtd.toLocaleString('pt-BR') },
  { chave: 'valorTotal', titulo: 'Valor Total (R$)', align: 'right', formatar: (i) => formatarBRL(i.valorTotal) },
  { chave: 'pct', titulo: '% do Total', align: 'right', formatar: (i) => formatarPct(i.pct) },
  { chave: 'valorMedio', titulo: 'Valor Médio (R$)', align: 'right', formatar: (i) => formatarBRL(i.valorMedio) },
]

const COLUNAS_FILIAL: ColunaTabela<{ filial: string; qtd: number; valorTotal: number; pct: number }>[] = [
  { chave: 'filial', titulo: 'Filial' },
  { chave: 'qtd', titulo: 'Qtd', align: 'right', formatar: (i) => i.qtd.toLocaleString('pt-BR') },
  { chave: 'valorTotal', titulo: 'Valor Total (R$)', align: 'right', formatar: (i) => formatarBRL(i.valorTotal) },
  { chave: 'pct', titulo: '% do Total', align: 'right', formatar: (i) => formatarPct(i.pct) },
]

const COLUNAS_DIA: ColunaTabela<Record<string, string>>[] = [
  { chave: 'dia', titulo: 'Dia' },
  { chave: 'emAberto', titulo: 'Em Aberto (R$)', align: 'right' },
  { chave: 'vencido', titulo: 'Vencido (R$)', align: 'right' },
  { chave: 'baixado', titulo: 'Baixado (R$)', align: 'right' },
  { chave: 'total', titulo: 'Total (R$)', align: 'right' },
]

export function FinanceiroPage() {
  const hoje = hojeAAAAMMDD()
  const [vencimentoDe, setVencimentoDe] = useState(hoje)
  const [vencimentoAte, setVencimentoAte] = useState('')
  const [status, setStatus] = useState('')

  const filtrosServidor = useMemo(
    () => ({ vencimentoDe, vencimentoAte: vencimentoAte || undefined, status: status || undefined }),
    [vencimentoDe, vencimentoAte, status],
  )

  const {
    dados, filial, setFilial, fornecedor, setFornecedor, tipo, setTipo,
    tipoOperacao, setTipoOperacao, categoria, setCategoria,
    isLoading, isFetching, isError, error, refetch,
  } = useFinanceiroData(filtrosServidor)

  const kpis = useMemo(() => calcularKpis(dados), [dados])
  const porStatus = useMemo(() => distribuicaoPorStatus(dados), [dados])
  const porFornecedor = useMemo(() => topFornecedoresPorSaldo(dados), [dados])
  const porMes = useMemo(() => saldoPorMesVencimento(dados), [dados])
  const porTipoOperacao = useMemo(() => saldoPorTipoOperacao(dados), [dados])
  const categoriaResumo = useMemo(() => resumoPorCategoria(dados), [dados])
  const filialResumo = useMemo(() => resumoPorFilial(dados), [dados])
  const evolucao = useMemo(() => resumoEvolucaoMensal(dados), [dados])
  const diaResumo = useMemo(() => resumoTotalPorDia(dados), [dados])

  const colunasEvolucao: ColunaTabela<Record<string, string>>[] = useMemo(
    () => [
      { chave: 'categoria', titulo: 'Categoria' },
      ...evolucao.colunasMes.map((c) => ({ chave: c.mesAno, titulo: c.titulo, align: 'right' as const })),
      { chave: 'total', titulo: 'Total', align: 'right' as const },
    ],
    [evolucao.colunasMes],
  )

  return (
    <Stack gap="md">
      <Group justify="space-between" wrap="wrap">
        <Title order={2}>Financeiro</Title>
        <ExportExcelButton
          href={urlExportacao({ ...filtrosServidor, filial, fornecedor, tipo, tipoOperacao, categoria })}
          disabled={dados.length === 0}
        />
      </Group>

      <Paper withBorder radius="md" p="md">
        <Stack gap="md">
          <PeriodoStatusToggle
            vencimentoDe={vencimentoDe}
            vencimentoAte={vencimentoAte}
            status={status}
            onChangeVencimentoDe={setVencimentoDe}
            onChangeVencimentoAte={setVencimentoAte}
            onChangeStatus={setStatus}
          />
          <Group gap="sm" wrap="wrap" align="flex-end">
            <TextInput label="Filial" value={filial} onChange={(e) => setFilial(e.currentTarget.value)} w={100} />
            <TextInput label="Fornecedor" value={fornecedor} onChange={(e) => setFornecedor(e.currentTarget.value)} w={220} />
            <TextInput label="Tipo" value={tipo} onChange={(e) => setTipo(e.currentTarget.value)} w={90} />
            <TextInput label="Tipo Operação" value={tipoOperacao} onChange={(e) => setTipoOperacao(e.currentTarget.value)} w={180} />
            <Select
              label="Categoria"
              value={categoria}
              data={CATEGORIA_OPCOES}
              onChange={(v) => setCategoria(v ?? '')}
              w={200}
              allowDeselect={false}
            />
            <Button variant="light" leftSection={<IconRefresh size={16} />} onClick={() => refetch()} loading={isFetching}>
              Atualizar
            </Button>
          </Group>
        </Stack>
      </Paper>

      {isError && (
        <Alert icon={<IconAlertCircle size={16} />} color="red" title="Erro ao carregar dados">
          {error instanceof Error ? error.message : 'Falha desconhecida ao consultar a API.'}
        </Alert>
      )}

      {isLoading ? (
        <Group justify="center" py="xl">
          <Loader />
        </Group>
      ) : (
        <>
          <KpiRow>
            <KpiCard label="Total de Títulos" value={kpis.totalTitulos.toLocaleString('pt-BR')} />
            <KpiCard label="Valor Total" value={formatarBRL(kpis.valorTotal)} color="#154360" />
            <KpiCard label="Recuperação Judicial" value={formatarBRL(kpis.recuperacaoJudicial)} color="#8e44ad" />
            <KpiCard label="Saldo Total" value={formatarBRL(kpis.saldoTotal)} color="#1a5276" />
            <KpiCard
              label="Em Aberto"
              value={kpis.emAbertoQtd.toLocaleString('pt-BR')}
              sublinha={formatarBRL(kpis.emAbertoSaldo)}
              color={STATUS_CORES['Em aberto']}
            />
            <KpiCard
              label="Vencidos"
              value={kpis.vencidosQtd.toLocaleString('pt-BR')}
              sublinha={formatarBRL(kpis.vencidosSaldo)}
              color={STATUS_CORES.Vencido}
            />
            <KpiCard
              label="Baixados"
              value={kpis.baixadosQtd.toLocaleString('pt-BR')}
              sublinha={formatarBRL(kpis.baixadosValor)}
              color={STATUS_CORES.Baixado}
            />
          </KpiRow>

          <Tabs defaultValue="graficos" keepMounted={false}>
            <Tabs.List>
              <Tabs.Tab value="graficos">Gráficos</Tabs.Tab>
              <Tabs.Tab value="dados">Dados</Tabs.Tab>
              <Tabs.Tab value="categoria">Por Categoria</Tabs.Tab>
              <Tabs.Tab value="evolucao">Evolução Mensal</Tabs.Tab>
              <Tabs.Tab value="dia">Total por Dia</Tabs.Tab>
              <Tabs.Tab value="filial">Por Filial</Tabs.Tab>
            </Tabs.List>

            <Tabs.Panel value="graficos" pt="md">
              <SimpleGrid cols={{ base: 1, md: 2 }} spacing="md">
                <PieChartCard
                  titulo="Distribuição por Status"
                  dados={porStatus}
                  formatarValor={(v) => v.toLocaleString('pt-BR')}
                  corPorRotulo={(r) => STATUS_CORES[r as keyof typeof STATUS_CORES] ?? '#bdc3c7'}
                />
                <HBarChart titulo="Top 10 Fornecedores — Saldo" dados={porFornecedor} formatarValor={formatarBRL} />
                <BarChartCard
                  titulo="Saldo por Mês de Vencimento (em aberto + vencidos)"
                  dados={porMes}
                  formatarValor={formatarBRL}
                  corPorRotulo={corSaldoPorMes}
                />
                <HBarChart titulo="Saldo por Tipo de Operação" dados={porTipoOperacao} formatarValor={formatarBRL} />
              </SimpleGrid>
            </Tabs.Panel>

            <Tabs.Panel value="dados" pt="md">
              <Paper withBorder radius="md" p="md">
                <ResponsiveTable
                  colunas={COLUNAS}
                  dados={dados}
                  chaveLinha={(i) => `${i.filial}-${i.numero}-${i.parcela}-${i.tipo}`}
                  destacarLinha={destacarLinha}
                />
              </Paper>
            </Tabs.Panel>

            <Tabs.Panel value="categoria" pt="md">
              <Stack gap="md">
                <HBarChart titulo="Valor Total por Categoria" dados={categoriaResumo.grafico} formatarValor={formatarBRL} corPorRotulo={corDaCategoria} />
                <Paper withBorder radius="md" p="md">
                  <Text size="sm" fw={600} mb="sm">
                    TOTAL GERAL — {categoriaResumo.total.qtd.toLocaleString('pt-BR')} títulos — {formatarBRL(categoriaResumo.total.valorTotal)}
                  </Text>
                  <ResponsiveTable colunas={COLUNAS_CATEGORIA} dados={categoriaResumo.linhas} chaveLinha={(i) => i.categoria} />
                </Paper>
              </Stack>
            </Tabs.Panel>

            <Tabs.Panel value="evolucao" pt="md">
              <Stack gap="md">
                <StackedBarChartCard
                  titulo="Evolução dos Custos por Categoria (mês de vencimento)"
                  dados={evolucao.graficoDados}
                  eixoX="mes"
                  series={evolucao.graficoSeries}
                  formatarValor={formatarBRL}
                />
                <Paper withBorder radius="md" p="md">
                  <Text size="sm" fw={600} mb="sm">
                    {evolucao.linhaTotal.categoria} — {evolucao.linhaTotal.total}
                  </Text>
                  <ResponsiveTable colunas={colunasEvolucao} dados={evolucao.linhas} chaveLinha={(i) => i.categoria} />
                </Paper>
              </Stack>
            </Tabs.Panel>

            <Tabs.Panel value="dia" pt="md">
              <Stack gap="md">
                <StackedBarChartCard
                  titulo="Total por Dia — A Pagar, Vencido e Baixado (dia de vencimento)"
                  dados={diaResumo.graficoDados}
                  eixoX="dia"
                  series={diaResumo.graficoSeries}
                  formatarValor={formatarBRL}
                />
                <Paper withBorder radius="md" p="md">
                  <Text size="sm" fw={600} mb="sm">
                    {diaResumo.linhaTotal.dia} — {diaResumo.linhaTotal.total}
                  </Text>
                  <ResponsiveTable colunas={COLUNAS_DIA} dados={diaResumo.linhas} chaveLinha={(i) => i.dia} />
                </Paper>
              </Stack>
            </Tabs.Panel>

            <Tabs.Panel value="filial" pt="md">
              <Stack gap="md">
                <PieChartCard titulo="Valor Total por Filial" dados={filialResumo.grafico} formatarValor={formatarBRL} />
                <Paper withBorder radius="md" p="md">
                  <Text size="sm" fw={600} mb="sm">
                    TOTAL GERAL — {filialResumo.total.qtd.toLocaleString('pt-BR')} títulos — {formatarBRL(filialResumo.total.valorTotal)}
                  </Text>
                  <ResponsiveTable colunas={COLUNAS_FILIAL} dados={filialResumo.linhas} chaveLinha={(i) => i.filial} />
                </Paper>
              </Stack>
            </Tabs.Panel>
          </Tabs>
        </>
      )}
    </Stack>
  )
}
