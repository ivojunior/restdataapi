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
import { formatarBRL, formatarQtd, paraNumero } from '../../utils/format'
import { urlExportacao } from './api'
import { calcularKpis } from './kpis'
import { quantidadePorFilial, topProdutosPorQuantidade, topProdutosPorValor, valorPorFilial } from './charts'
import { TIPO_ESTOQUE_OPCOES, TipoEstoqueSelector } from './TipoEstoqueSelector'
import type { EstoqueItem } from './types'
import { useEstoqueData } from './useEstoqueData'

const COLUNAS: ColunaTabela<EstoqueItem>[] = [
  { chave: 'filial', titulo: 'Filial' },
  { chave: 'local', titulo: 'Local' },
  { chave: 'codigo_produto', titulo: 'Código Produto' },
  { chave: 'descricao_produto', titulo: 'Descrição' },
  { chave: 'quantidade', titulo: 'Quantidade', align: 'right', formatar: (i) => formatarQtd(Number(i.quantidade)) },
  { chave: 'valor_atual', titulo: 'Valor Atual (R$)', align: 'right', formatar: (i) => formatarBRL(paraNumero(i.valor_atual)) },
]

export function EstoquePage() {
  const [tipoRotulo, setTipoRotulo] = useState(Object.keys(TIPO_ESTOQUE_OPCOES)[0])
  const filtrosServidor = TIPO_ESTOQUE_OPCOES[tipoRotulo]

  const {
    dados, filial, setFilial, codigo, setCodigo, descricao, setDescricao,
    isLoading, isFetching, isError, error, refetch,
  } = useEstoqueData(filtrosServidor)

  const kpis = useMemo(() => calcularKpis(dados), [dados])
  const topValor = useMemo(() => topProdutosPorValor(dados), [dados])
  const topQuantidade = useMemo(() => topProdutosPorQuantidade(dados), [dados])
  const porFilialValor = useMemo(() => valorPorFilial(dados), [dados])
  const porFilialQuantidade = useMemo(() => quantidadePorFilial(dados), [dados])

  return (
    <Stack gap="md">
      <Group justify="space-between" wrap="wrap">
        <Title order={2}>Saldo de Estoque</Title>
        <ExportExcelButton
          href={urlExportacao({ ...filtrosServidor, filial, codigo, descricao })}
          disabled={dados.length === 0}
        />
      </Group>

      <Paper withBorder radius="md" p="md">
        <Group justify="space-between" wrap="wrap" gap="md" align="flex-end">
          <TipoEstoqueSelector rotulo={tipoRotulo} onChange={setTipoRotulo} />
          <Group gap="sm" wrap="wrap" align="flex-end">
            <TextInput
              label="Filial"
              value={filial}
              onChange={(evento) => setFilial(evento.currentTarget.value)}
              w={100}
            />
            <TextInput
              label="Código"
              value={codigo}
              onChange={(evento) => setCodigo(evento.currentTarget.value)}
              w={150}
            />
            <TextInput
              label="Descrição"
              value={descricao}
              onChange={(evento) => setDescricao(evento.currentTarget.value)}
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
            <KpiCard label="Itens em Estoque" value={kpis.totalItens.toLocaleString('pt-BR')} />
            <KpiCard label="Filiais" value={kpis.filiais.toLocaleString('pt-BR')} />
            <KpiCard label="Quantidade Total" value={formatarQtd(kpis.quantidadeTotal)} />
            <KpiCard label="Valor Total" value={formatarBRL(kpis.valorTotal)} color="#154360" />
            <KpiCard label="Valor Médio / Item" value={formatarBRL(kpis.valorMedio)} color="#1e8449" />
          </KpiRow>

          <SimpleGrid cols={{ base: 1, md: 2 }} spacing="md">
            <HBarChart titulo="Top 10 Produtos — Valor em Estoque" dados={topValor} formatarValor={formatarBRL} />
            <PieChartCard titulo="Valor Total por Filial" dados={porFilialValor} formatarValor={formatarBRL} />
            <HBarChart titulo="Top 10 Produtos — Quantidade em Estoque" dados={topQuantidade} formatarValor={formatarQtd} />
            <BarChartCard titulo="Quantidade Total por Filial" dados={porFilialQuantidade} formatarValor={formatarQtd} />
          </SimpleGrid>

          <Paper withBorder radius="md" p="md">
            <Text fw={600} size="sm" mb="sm">
              Dados
            </Text>
            <ResponsiveTable
              colunas={COLUNAS}
              dados={dados}
              chaveLinha={(i) => `${i.filial}-${i.local}-${i.codigo_produto}`}
            />
          </Paper>
        </>
      )}
    </Stack>
  )
}
