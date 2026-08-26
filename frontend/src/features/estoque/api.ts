import { apiClient } from '../../api/client'
import type { PaginatedResponse } from '../../api/types'
import type { EstoqueItem } from './types'

const TAMANHO_PAGINA = 200

export interface FiltrosTipoEstoque {
  tipoProduto: string
  local: string
}

function montarQuery(params: Record<string, string | number | undefined>): string {
  const busca = new URLSearchParams()
  for (const [chave, valor] of Object.entries(params)) {
    if (valor !== undefined && valor !== '') busca.set(chave, String(valor))
  }
  const texto = busca.toString()
  return texto ? `?${texto}` : ''
}

/** Busca todas as páginas de /saldos-estoque/ para o tipo/local escolhidos
 * (loop até vir uma página vazia) — mesma estratégia de
 * client/api_client.py:get_all_saldos_estoque. */
export async function buscarTodoEstoque(
  { tipoProduto, local }: FiltrosTipoEstoque,
  onProgresso?: (carregados: number) => void,
): Promise<EstoqueItem[]> {
  const itens: EstoqueItem[] = []
  let skip = 0

  // eslint-disable-next-line no-constant-condition
  while (true) {
    const query = montarQuery({
      skip, limit: TAMANHO_PAGINA, tipo_produto: tipoProduto, local,
    })
    const pagina = await apiClient.get<PaginatedResponse<EstoqueItem>>(`/saldos-estoque/${query}`)
    itens.push(...pagina.items)
    skip += pagina.items.length
    onProgresso?.(itens.length)
    if (pagina.items.length === 0) break
  }

  return itens
}

export function urlExportacao(
  filtros: FiltrosTipoEstoque & { filial?: string; codigo?: string; descricao?: string },
): string {
  const query = montarQuery({
    tipo_produto: filtros.tipoProduto,
    local: filtros.local,
    filial: filtros.filial,
    codigo: filtros.codigo,
    descricao: filtros.descricao,
  })
  return `/saldos-estoque/export${query}`
}
