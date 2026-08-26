import { Select } from '@mantine/core'

// Rótulo exibido -> (tipo_produto, local) enviados como query string à API.
// Réplica de TIPO_ESTOQUE_OPCOES em client/app_estoque.py.
const TIPO_ESTOQUE_OPCOES: Record<string, { tipoProduto: string; local: string }> = {
  'Produtos Acabados (Tipo PA — Armazém 01)': { tipoProduto: 'PA', local: '01' },
  'Vasilhames (Tipo AM — Armazém 20)': { tipoProduto: 'AM', local: '20' },
}

export { TIPO_ESTOQUE_OPCOES }

export function TipoEstoqueSelector({
  rotulo, onChange,
}: {
  rotulo: string
  onChange: (rotulo: string) => void
}) {
  return (
    <Select
      label="Tipo de Estoque"
      description="A escolha define tipo_produto/local enviados à API"
      value={rotulo}
      data={Object.keys(TIPO_ESTOQUE_OPCOES)}
      onChange={(valor) => valor && onChange(valor)}
      w={320}
      allowDeselect={false}
    />
  )
}
