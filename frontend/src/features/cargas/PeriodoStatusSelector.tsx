import { Group, Select, TextInput } from '@mantine/core'
import { deInputDate, paraInputDate } from '../../utils/date'

const STATUS_OPCOES = [
  { value: '', label: '(Todos)' },
  { value: 'aberta', label: 'Aberta' },
  { value: 'encerrada', label: 'Fechada' },
]

export function PeriodoStatusSelector({
  dataInicial, dataFinal, status, onChangeDataInicial, onChangeDataFinal, onChangeStatus,
}: {
  dataInicial: string
  dataFinal: string
  status: string
  onChangeDataInicial: (aaaammdd: string) => void
  onChangeDataFinal: (aaaammdd: string) => void
  onChangeStatus: (status: string) => void
}) {
  return (
    <Group gap="sm" wrap="wrap" align="flex-end">
      <TextInput
        type="date"
        label="Data de"
        value={paraInputDate(dataInicial)}
        onChange={(evento) => onChangeDataInicial(deInputDate(evento.currentTarget.value))}
        w={160}
      />
      <TextInput
        type="date"
        label="Data até"
        value={paraInputDate(dataFinal)}
        onChange={(evento) => onChangeDataFinal(deInputDate(evento.currentTarget.value))}
        w={160}
      />
      <Select
        label="Status"
        value={status}
        data={STATUS_OPCOES}
        onChange={(valor) => onChangeStatus(valor ?? '')}
        w={140}
        allowDeselect={false}
      />
    </Group>
  )
}
