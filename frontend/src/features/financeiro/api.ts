import { apiClient } from '../../api/client'
import type { PaginatedResponse } from '../../api/types'
import type { FinanceiroItem } from './types'

const TAMANHO_PAGINA = 200

export interface FiltrosServidorFinanceiro {
  vencimentoDe?: string
  vencimentoAte?: string
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

/** Busca todas as páginas de /financeiro/ para o período/status escolhidos
 * (loop até vir uma página vazia) — mesma estratégia de
 * client/api_client.py:get_all_financeiro. */
export async function buscarTodoFinanceiro(
  { vencimentoDe, vencimentoAte, status }: FiltrosServidorFinanceiro,
  onProgresso?: (carregados: number) => void,
): Promise<FinanceiroItem[]> {
  const itens: FinanceiroItem[] = []
  let skip = 0

  // eslint-disable-next-line no-constant-condition
  while (true) {
    const query = montarQuery({
      skip, limit: TAMANHO_PAGINA, vencimento_de: vencimentoDe,
      vencimento_ate: vencimentoAte, status,
    })
    const pagina = await apiClient.get<PaginatedResponse<FinanceiroItem>>(`/financeiro/${query}`)
    itens.push(...pagina.items)
    skip += pagina.items.length
    onProgresso?.(itens.length)
    if (pagina.items.length === 0) break
  }

  return itens
}

export function urlExportacao(
  filtros: FiltrosServidorFinanceiro & {
    filial?: string
    fornecedor?: string
    tipo?: string
    tipoOperacao?: string
    categoria?: string
  },
): string {
  const query = montarQuery({
    vencimento_de: filtros.vencimentoDe,
    vencimento_ate: filtros.vencimentoAte,
    status: filtros.status,
    filial: filtros.filial,
    fornecedor: filtros.fornecedor,
    tipo: filtros.tipo,
    tipo_operacao: filtros.tipoOperacao,
    categoria: filtros.categoria,
  })
  return `/financeiro/export${query}`
}
