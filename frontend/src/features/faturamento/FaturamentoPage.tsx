import { Alert, Button, Group, Loader, Paper, SimpleGrid, Stack, Text, TextInput, Title } from '@mantine/core'
import { IconAlertCircle, IconRefresh } from '@tabler/icons-react'
import { useMemo, useState } from 'react'
import { BarChartCard } from '../../components/charts/BarChartCard'
import { HBarChart } from '../../components/charts/HBarChart'
import { PieChartCard } from '../../components/charts/PieChartCard'
import { ResponsiveTable, type ColunaTabela } from '../../components/data-table/ResponsiveTable'
import { ExportExcelButton } from '../../components/export/ExportExcelButton'
import { KpiCard } from '../../components/kpi/KpiCard'
import { KpiRow } from '../../components/kpi/KpiRow'
import { periodoDoMes } from '../../utils/date'
import { formatarBRL, formatarPct, formatarQtd, paraNumero } from '../../utils/format'
import { urlExportacao } from './api'
import { calcularKpis } from './kpis'
import { faturamentoPorDia, faturamentoPorFilial, topProdutosPorFaturamento, topProdutosPorLucro } from './charts'
import { PeriodoSelector } from './PeriodoSelector'
import type { FaturamentoItem } from './types'
import { useFaturamentoData } from './useFaturamentoData'

const COLUNAS: ColunaTabela<FaturamentoItem>[] = [
  { chave: 'filial', titulo: 'Filial' },
  { chave: 'dia', titulo: 'Dia', align: 'center' },
  { chave: 'codigo', titulo: 'Código' },
  { chave: 'descricao', titulo: 'Descrição' },
  { chave: 'quantidade', titulo: 'Quantidade', align: 'right', formatar: (i) => formatarQtd(Number(i.quantidade)) },
  { chave: 'faturamento', titulo: 'Faturamento (R$)', align: 'right', formatar: (i) => formatarBRL(Number(i.faturamento)) },
  { chave: 'custo', titulo: 'Custo (R$)', align: 'right', formatar: (i) => formatarBRL(Number(i.custo)) },
  { chave: 'preco_medio', titulo: 'Preço Médio (R$)', align: 'right', formatar: (i) => formatarBRL(paraNumero(i.preco_medio)) },
  { chave: 'lucro_bruto', titulo: 'Lucro Bruto (R$)', align: 'right', formatar: (i) => formatarBRL(Number(i.lucro_bruto)) },
  { chave: 'margem', titulo: 'Margem (%)', align: 'right', formatar: (i) => formatarPct(paraNumero(i.margem)) },
  { chave: 'markup', titulo: 'Markup (%)', align: 'right', formatar: (i) => formatarPct(paraNumero(i.markup)) },
]

export function FaturamentoPage() {
  const hoje = new Date()
  const [mes, setMes] = useState(hoje.getMonth() + 1)
  const [ano, setAno] = useState(hoje.getFullYear())

  // `dia` na API é só o dia do mês (não uma data completa) — por isso esta
  // tela sempre consulta um único mês por vez, senão dias iguais de meses
  // diferentes apareceriam somados na mesma linha (comportamento da API;
  // ver app/routers/faturamento.py e o client desktop equivalente).
  const periodo = useMemo(() => periodoDoMes(ano, mes), [ano, mes])

  const {
    dados, filial, setFilial, produto, setProduto,
    isLoading, isFetching, isError, error, refetch,
  } = useFaturamentoData(periodo)

  const kpis = useMemo(() => calcularKpis(dados), [dados])
  const topFaturamento = useMemo(() => topProdutosPorFaturamento(dados), [dados])
  const topLucro = useMemo(() => topProdutosPorLucro(dados), [dados])
  const porFilial = useMemo(() => faturamentoPorFilial(dados), [dados])
  const porDia = useMemo(() => faturamentoPorDia(dados), [dados])

  return (
    <Stack gap="md">
      <Group justify="space-between" wrap="wrap">
        <Title order={2}>Faturamento</Title>
        <ExportExcelButton
          href={urlExportacao({ ...periodo, filial, produto })}
          disabled={dados.length === 0}
        />
      </Group>

      <Paper withBorder radius="md" p="md">
        <Group justify="space-between" wrap="wrap" gap="md" align="flex-end">
          <PeriodoSelector mes={mes} ano={ano} onChangeMes={setMes} onChangeAno={setAno} />
          <Group gap="sm" wrap="wrap" align="flex-end">
            <TextInput
              label="Filial"
              value={filial}
              onChange={(evento) => setFilial(evento.currentTarget.value)}
              w={100}
            />
            <TextInput
              label="Produto"
              placeholder="Código ou descrição"
              value={produto}
              onChange={(evento) => setProduto(evento.currentTarget.value)}
              w={220}
            />
            <Button
              variant="light"
              leftSection={<IconRefresh size={16} />}
              onClick={() => refetch()}
              loading={isFetching}
            >
              Atualizar
            </Button>
          </Group>
        </Group>
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
            <KpiCard label="Registros" value={kpis.registros.toLocaleString('pt-BR')} />
            <KpiCard label="Produtos" value={kpis.produtos.toLocaleString('pt-BR')} />
            <KpiCard label="Quantidade Total" value={formatarQtd(kpis.quantidadeTotal)} />
            <KpiCard label="Faturamento Total" value={formatarBRL(kpis.faturamentoTotal)} color="#154360" />
            <KpiCard label="Custo Total" value={formatarBRL(kpis.custoTotal)} color="#943126" />
            <KpiCard label="Preço Médio Acumulado" value={formatarBRL(kpis.precoMedioAcumulado)} color="#6c3483" />
            <KpiCard label="Lucro Bruto Total" value={formatarBRL(kpis.lucroBrutoTotal)} color="#1e8449" />
            <KpiCard label="Margem Geral" value={formatarPct(kpis.margemGeral)} color="#ca6f1e" />
            <KpiCard label="Markup Geral" value={formatarPct(kpis.markupGeral)} color="#b9770e" />
          </KpiRow>

          <SimpleGrid cols={{ base: 1, md: 2 }} spacing="md">
            <HBarChart titulo="Top 10 Produtos — Faturamento" dados={topFaturamento} formatarValor={formatarBRL} />
            <PieChartCard titulo="Faturamento Total por Filial" dados={porFilial} formatarValor={formatarBRL} />
            <BarChartCard titulo="Faturamento por Dia do Mês" dados={porDia} formatarValor={formatarBRL} />
            <HBarChart titulo="Top 10 Produtos — Lucro Bruto" dados={topLucro} formatarValor={formatarBRL} />
          </SimpleGrid>

          <Paper withBorder radius="md" p="md">
            <Text fw={600} size="sm" mb="sm">
              Dados
            </Text>
            <ResponsiveTable colunas={COLUNAS} dados={dados} chaveLinha={(i) => `${i.filial}-${i.dia}-${i.codigo}`} />
          </Paper>
        </>
      )}
    </Stack>
  )
}
