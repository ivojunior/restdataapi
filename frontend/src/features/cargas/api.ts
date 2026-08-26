import { apiClient } from '../../api/client'
import type { PaginatedResponse } from '../../api/types'
import type { CargaItem } from './types'

const TAMANHO_PAGINA = 200

export interface FiltrosServidorCargas {
  dataInicial: string
  dataFinal: string
  status?: string
}

function montarQuery(params: Record<string, string | number | undefined>): string {
  const busca = new URLSearchParams()
  for (const [chave, valor] of Object.entries(params)) {
    if (valor !== undefined && valor !== '') busca.set(chave, String(valor))
  }
  const texto = busca.toString()
  return texto ? `?${texto}` : ''
}

/** Busca todas as páginas de /cargas/ para o período/status escolhidos
 * (loop até vir uma página vazia) — mesma estratégia de
 * client/api_client.py:get_all_cargas. */
export async function buscarTodasCargas(
  { dataInicial, dataFinal, status }: FiltrosServidorCargas,
  onProgresso?: (carregados: number) => void,
): Promise<CargaItem[]> {
  const itens: CargaItem[] = []
  let skip = 0

  // eslint-disable-next-line no-constant-condition
  while (true) {
    const query = montarQuery({
      skip, limit: TAMANHO_PAGINA, data_inicial: dataInicial, data_final: dataFinal, status,
    })
    const pagina = await apiClient.get<PaginatedResponse<CargaItem>>(`/cargas/${query}`)
    itens.push(...pagina.items)
    skip += pagina.items.length
    onProgresso?.(itens.length)
    if (pagina.items.length === 0) break
  }

  return itens
}

export function urlExportacao(
  filtros: FiltrosServidorCargas & { filial?: string; cliente?: string; caminhao?: string },
): string {
  const query = montarQuery({
    data_inicial: filtros.dataInicial,
    data_final: filtros.dataFinal,
    status: filtros.status,
    filial: filtros.filial,
    cliente: filtros.cliente,
    caminhao: filtros.caminhao,
  })
  return `/cargas/export${query}`
}
