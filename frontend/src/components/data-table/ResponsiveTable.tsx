import { Card, ScrollArea, Stack, Table, Text, UnstyledButton } from '@mantine/core'
import { useMediaQuery } from '@mantine/hooks'
import { IconChevronDown, IconChevronUp, IconSelector } from '@tabler/icons-react'
import { useState } from 'react'

export interface ColunaTabela<T> {
  chave: keyof T
  titulo: string
  align?: 'left' | 'right' | 'center'
  formatar?: (item: T) => string
}

/** Tabela genérica com um único componente para desktop (Mantine Table,
 * ordenável por clique no cabeçalho — mesmo padrão dos Treeview dos
 * clients desktop) e mobile (lista de cards empilhados, rótulo: valor —
 * evita scroll horizontal ilegível em tela estreita). */
export function ResponsiveTable<T>({
  colunas, dados, chaveLinha,
}: {
  colunas: ColunaTabela<T>[]
  dados: T[]
  chaveLinha: (item: T) => string
}) {
  const [ordenacao, setOrdenacao] = useState<{ chave: keyof T; asc: boolean } | null>(null)
  const empilhado = useMediaQuery('(max-width: 48em)') ?? false

  function alternarOrdenacao(chave: keyof T) {
    setOrdenacao((atual) => (atual?.chave === chave ? { chave, asc: !atual.asc } : { chave, asc: true }))
  }

  const dadosOrdenados = ordenacao
    ? [...dados].sort((a, b) => {
        const va = a[ordenacao.chave]
        const vb = b[ordenacao.chave]
        const cmp =
          typeof va === 'number' && typeof vb === 'number'
            ? va - vb
            : String(va).localeCompare(String(vb), 'pt-BR')
        return ordenacao.asc ? cmp : -cmp
      })
    : dados

  if (dados.length === 0) {
    return (
      <Text c="dimmed" ta="center" py="xl">
        Nenhum registro para os filtros atuais.
      </Text>
    )
  }

  if (empilhado) {
    return (
      <Stack gap="xs">
        {dadosOrdenados.map((item) => (
          <Card key={chaveLinha(item)} withBorder radius="md" padding="sm">
            <Stack gap={4}>
              {colunas.map((coluna) => (
                <div key={String(coluna.chave)} style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                  <Text size="xs" c="dimmed">
                    {coluna.titulo}
                  </Text>
                  <Text size="sm" fw={500} ta="right">
                    {coluna.formatar ? coluna.formatar(item) : String(item[coluna.chave] ?? '')}
                  </Text>
                </div>
              ))}
            </Stack>
          </Card>
        ))}
      </Stack>
    )
  }

  return (
    <ScrollArea>
      <Table striped highlightOnHover withTableBorder>
        <Table.Thead>
          <Table.Tr>
            {colunas.map((coluna) => (
              <Table.Th key={String(coluna.chave)}>
                <UnstyledButton
                  onClick={() => alternarOrdenacao(coluna.chave)}
                  style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}
                >
                  <Text size="sm" fw={600} ta={coluna.align ?? 'left'}>
                    {coluna.titulo}
                  </Text>
                  {ordenacao?.chave === coluna.chave ? (
                    ordenacao.asc ? <IconChevronUp size={12} /> : <IconChevronDown size={12} />
                  ) : (
                    <IconSelector size={12} opacity={0.4} />
                  )}
                </UnstyledButton>
              </Table.Th>
            ))}
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {dadosOrdenados.map((item) => (
            <Table.Tr key={chaveLinha(item)}>
              {colunas.map((coluna) => (
                <Table.Td key={String(coluna.chave)} ta={coluna.align ?? 'left'}>
                  {coluna.formatar ? coluna.formatar(item) : String(item[coluna.chave] ?? '')}
                </Table.Td>
              ))}
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </ScrollArea>
  )
}
