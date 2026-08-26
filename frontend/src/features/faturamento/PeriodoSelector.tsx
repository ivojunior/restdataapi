import { Group, Select } from '@mantine/core'

const MESES = [
  '01 - Janeiro', '02 - Fevereiro', '03 - Março', '04 - Abril',
  '05 - Maio', '06 - Junho', '07 - Julho', '08 - Agosto',
  '09 - Setembro', '10 - Outubro', '11 - Novembro', '12 - Dezembro',
]

export function PeriodoSelector({
  mes, ano, onChangeMes, onChangeAno,
}: {
  mes: number
  ano: number
  onChangeMes: (mes: number) => void
  onChangeAno: (ano: number) => void
}) {
  const anoAtual = new Date().getFullYear()
  const anos = Array.from({ length: 7 }, (_, i) => String(anoAtual - 5 + i))

  return (
    <Group gap="sm" wrap="nowrap">
      <Select
        label="Mês"
        value={MESES[mes - 1]}
        data={MESES}
        onChange={(valor) => valor && onChangeMes(MESES.indexOf(valor) + 1)}
        w={160}
        allowDeselect={false}
      />
      <Select
        label="Ano"
        value={String(ano)}
        data={anos}
        onChange={(valor) => valor && onChangeAno(Number(valor))}
        w={100}
        allowDeselect={false}
      />
    </Group>
  )
}
