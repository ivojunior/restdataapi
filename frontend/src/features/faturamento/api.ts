import { apiClient } from '../../api/client'
import type { PaginatedResponse } from '../../api/types'
import type { FaturamentoItem } from './types'

const TAMANHO_PAGINA = 200

export interface FiltrosPeriodo {
  dataInicial: string
  dataFinal: string
}

function montarQuery(params: Record<string, string | number | undefined>): string {
  const busca = new URLSearchParams()
  for (const [chave, valor] of Object.entries(params)) {
    if (valor !== undefined && valor !== '') busca.set(chave, String(valor))
  }
  const texto = busca.toString()
  return texto ? `?${texto}` : ''
}

/** Busca todas as páginas de /faturamento/ para o período (loop até vir uma
 * página vazia) — mesma estratégia de client/api_client.py:get_all_faturamento,
 * já que a API não expõe count(*) total (ver README da raiz). */
export async function buscarTodoFaturamento(
  { dataInicial, dataFinal }: FiltrosPeriodo,
  onProgresso?: (carregados: number) => void,
): Promise<FaturamentoItem[]> {
  const itens: FaturamentoItem[] = []
  let skip = 0

  // eslint-disable-next-line no-constant-condition
  while (true) {
    const query = montarQuery({
      skip, limit: TAMANHO_PAGINA, data_inicial: dataInicial, data_final: dataFinal,
    })
    const pagina = await apiClient.get<PaginatedResponse<FaturamentoItem>>(`/faturamento/${query}`)
    itens.push(...pagina.items)
    skip += pagina.items.length
    onProgresso?.(itens.length)
    if (pagina.items.length === 0) break
  }

  return itens
}

export function urlExportacao(filtros: FiltrosPeriodo & { filial?: string; produto?: string }): string {
  const query = montarQuery({
    data_inicial: filtros.dataInicial,
    data_final: filtros.dataFinal,
    filial: filtros.filial,
    produto: filtros.produto,
  })
  return `/faturamento/export${query}`
}
