import { Group, Select, TextInput } from '@mantine/core'
import { deInputDate, paraInputDate } from '../../utils/date'

// Rótulo exibido -> valor aceito pelo parâmetro "status" de GET /financeiro/
// — réplica de STATUS_API_VALUES em client/app_financeiro.py.
const STATUS_OPCOES = [
  { value: '', label: '(Todos)' },
  { value: 'em_aberto', label: 'Em aberto' },
  { value: 'vencido', label: 'Vencido' },
  { value: 'baixado', label: 'Baixado' },
]

export function PeriodoStatusToggle({
  vencimentoDe, vencimentoAte, status, onChangeVencimentoDe, onChangeVencimentoAte, onChangeStatus,
}: {
  vencimentoDe: string
  vencimentoAte: string
  status: string
  onChangeVencimentoDe: (aaaammdd: string) => void
  onChangeVencimentoAte: (aaaammdd: string) => void
  onChangeStatus: (status: string) => void
}) {
  return (
    <Group gap="sm" wrap="wrap" align="flex-end">
      <TextInput
        type="date"
        label="Vencimento de"
        value={paraInputDate(vencimentoDe)}
        onChange={(evento) => onChangeVencimentoDe(deInputDate(evento.currentTarget.value))}
        w={170}
      />
      <TextInput
        type="date"
        label="Vencimento até"
        value={paraInputDate(vencimentoAte)}
        onChange={(evento) => onChangeVencimentoAte(deInputDate(evento.currentTarget.value))}
        w={170}
      />
      <Select
        label="Status"
        value={status}
        data={STATUS_OPCOES}
        onChange={(valor) => onChangeStatus(valor ?? '')}
        w={150}
        allowDeselect={false}
      />
    </Group>
  )
}
