import { Alert, Button, Group, Loader, Paper, SimpleGrid, Stack, Text, TextInput, Title } from '@mantine/core'
import { IconAlertCircle, IconRefresh } from '@tabler/icons-react'
import { useMemo, useState } from 'react'
import { BarChartCard } from '../../components/charts/BarChartCard'
import { HBarChart } from '../../components/charts/HBarChart'
import { PieChartCard } from '../../components/charts/PieChartCard'
import { ResponsiveTable, type ColunaTabela, type EstiloLinha } from '../../components/data-table/ResponsiveTable'
import { ExportExcelButton } from '../../components/export/ExportExcelButton'
import { KpiCard } from '../../components/kpi/KpiCard'
import { KpiRow } from '../../components/kpi/KpiRow'
import { diferencaEmDiasDeHoje, hojeAAAAMMDD } from '../../utils/date'
import { formatarBRL, formatarDataBR, formatarQtd, ouTraco } from '../../utils/format'
import { urlExportacao } from './api'
import { cargasPorData, topCaminhoesPorPeso, topClientesPorValor, valorPorFilial } from './charts'
import { calcularKpis } from './kpis'
import { PeriodoStatusSelector } from './PeriodoStatusSelector'
import { chaveCarga, type CargaItem } from './types'
import { useCargasData } from './useCargasData'

const COLUNAS: ColunaTabela<CargaItem>[] = [
  { chave: 'filial', titulo: 'Filial' },
  { chave: 'codigo', titulo: 'Carga' },
  { chave: 'data', titulo: 'Data', align: 'center', formatar: (i) => formatarDataBR(i.data) },
  { chave: 'pedido', titulo: 'Pedido' },
  { chave: 'motorista', titulo: 'Motorista', formatar: (i) => ouTraco(i.motorista) },
  { chave: 'nome_cliente', titulo: 'Cliente', formatar: (i) => ouTraco(i.nome_cliente) },
  { chave: 'bairro_cliente', titulo: 'Bairro', formatar: (i) => ouTraco(i.bairro_cliente) },
  { chave: 'municipio_cliente', titulo: 'Município', formatar: (i) => ouTraco(i.municipio_cliente) },
  { chave: 'nota_fiscal', titulo: 'Nota Fiscal', align: 'center' },
  { chave: 'caminhao', titulo: 'Caminhão', align: 'center' },
  { chave: 'status_carga', titulo: 'Status', align: 'center' },
  { chave: 'peso', titulo: 'Peso (kg)', align: 'right', formatar: (i) => formatarQtd(Number(i.peso)) },
  { chave: 'valor', titulo: 'Valor (R$)', align: 'right', formatar: (i) => formatarBRL(Number(i.valor)) },
]

// Linhas de carga "Aberta" cuja Data está a mais de 3 dias (pra trás ou pra
// frente) da data do sistema ficam com o texto em vermelho e negrito —
// réplica da tag "data_distante" do Treeview em client/app_cargas.py (uma
// carga "Fechada" com data distante já foi resolvida, não precisa mais
// chamar atenção do usuário).
function destacarLinha(item: CargaItem): EstiloLinha | undefined {
  const dias = diferencaEmDiasDeHoje(item.data)
  return dias > 3 && item.status_carga === 'Aberta' ? { corTexto: '#e74c3c', negrito: true } : undefined
}

export function CargasPage() {
  const hoje = hojeAAAAMMDD()
  const [dataInicial, setDataInicial] = useState(hoje)
  const [dataFinal, setDataFinal] = useState(hoje)
  const [status, setStatus] = useState('')

  const filtrosServidor = useMemo(
    () => ({ dataInicial, dataFinal, status: status || undefined }),
    [dataInicial, dataFinal, status],
  )

  const {
    dados, filial, setFilial, cliente, setCliente, caminhao, setCaminhao,
    isLoading, isFetching, isError, error, refetch,
  } = useCargasData(filtrosServidor)

  const kpis = useMemo(() => calcularKpis(dados), [dados])
  const topClientes = useMemo(() => topClientesPorValor(dados), [dados])
  const porFilial = useMemo(() => valorPorFilial(dados), [dados])
  const porData = useMemo(() => cargasPorData(dados), [dados])
  const topCaminhoes = useMemo(() => topCaminhoesPorPeso(dados), [dados])

  return (
    <Stack gap="md">
      <Group justify="space-between" wrap="wrap">
        <Title order={2}>Cargas</Title>
        <ExportExcelButton
          href={urlExportacao({ ...filtrosServidor, filial, cliente, caminhao })}
          disabled={dados.length === 0}
        />
      </Group>

      <Paper withBorder radius="md" p="md">
        <Stack gap="md">
          <PeriodoStatusSelector
            dataInicial={dataInicial}
            dataFinal={dataFinal}
            status={status}
            onChangeDataInicial={setDataInicial}
            onChangeDataFinal={setDataFinal}
            onChangeStatus={setStatus}
          />
          <Group gap="sm" wrap="wrap" align="flex-end">
            <TextInput
              label="Filial"
              value={filial}
              onChange={(evento) => setFilial(evento.currentTarget.value)}
              w={100}
            />
            <TextInput
              label="Cliente"
              value={cliente}
              onChange={(evento) => setCliente(evento.currentTarget.value)}
              w={220}
            />
            <TextInput
              label="Caminhão"
              value={caminhao}
              onChange={(evento) => setCaminhao(evento.currentTarget.value)}
              w={150}
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
            <KpiCard label="Total de Cargas" value={kpis.totalCargas.toLocaleString('pt-BR')} />
            <KpiCard label="Pedidos" value={kpis.pedidos.toLocaleString('pt-BR')} />
            <KpiCard label="Peso Total (kg)" value={formatarQtd(kpis.pesoTotal)} color="#1a5276" />
            <KpiCard label="Valor Total" value={formatarBRL(kpis.valorTotal)} color="#154360" />
            <KpiCard label="Valor em Aberto" value={formatarBRL(kpis.valorAberto)} color="#ca6f1e" />
            <KpiCard label="Valor Acertado" value={formatarBRL(kpis.valorAcertado)} color="#117864" />
            <KpiCard label="Valor Médio/Carga" value={formatarBRL(kpis.valorMedio)} color="#1e8449" />
          </KpiRow>

          <SimpleGrid cols={{ base: 1, md: 2 }} spacing="md">
            <HBarChart titulo="Top 10 Clientes — Valor Faturado" dados={topClientes} formatarValor={formatarBRL} />
            <PieChartCard titulo="Valor Total por Filial" dados={porFilial} formatarValor={formatarBRL} />
            <BarChartCard titulo="Nº de Cargas por Data (últimas 12 datas)" dados={porData} formatarValor={(v) => String(Math.round(v))} />
            <HBarChart titulo="Top 10 Caminhões — Peso Transportado" dados={topCaminhoes} formatarValor={formatarQtd} />
          </SimpleGrid>

          <Paper withBorder radius="md" p="md">
            <Text fw={600} size="sm" mb="sm">
              Dados
            </Text>
            <ResponsiveTable
              colunas={COLUNAS}
              dados={dados}
              chaveLinha={(i) => `${chaveCarga(i)}-${i.nota_fiscal}-${i.pedido}`}
              destacarLinha={destacarLinha}
            />
          </Paper>
        </>
      )}
    </Stack>
  )
}
