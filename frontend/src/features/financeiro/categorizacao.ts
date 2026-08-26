import regrasBrutas from './categorias.json'

/** Categorização de títulos — réplica de client/categorias.py, lendo as
 * regras de categorias.json (cópia estática extraída de
 * client/categorias.xlsx, empacotada no build da SPA) em vez de um .xlsx
 * editável.
 *
 * A mesma categorização também existe no backend (ver
 * app/excel/categorizacao_financeiro.py, usado só na exportação Excel),
 * copiada da mesma fonte original — as duas cópias podem divergir se
 * alguém editar client/categorias.xlsx sem atualizar as duas. Não há hoje
 * um mecanismo que as mantenha sincronizadas automaticamente. */

export const CATEGORIAS_CANONICAS = [
  'Fornecedor', 'Imposto', 'Jurídico', 'Manutenção Automotiva',
  'Prestador de Serviço', 'T.I.', 'Combustível', 'Outros',
] as const

export const NAO_CLASSIFICADO = 'Não Classificado'

interface Regra {
  fornecedor: string
  historico: string
  categoria: string
}

function normalizar(valor: string | null | undefined): string {
  // \p{Mn}: marcas diacríticas combinantes (acentos) após NFD — mesmo
  // filtro de unicodedata.category(c) != "Mn" em client/categorias.py.
  return (valor ?? '')
    .normalize('NFD')
    .replace(/\p{Mn}/gu, '')
    .trim()
    .toLowerCase()
}

const REGRAS: Regra[] = (regrasBrutas as { fornecedor: string; historico: string; categoria: string }[]).map(
  (r) => ({
    fornecedor: normalizar(r.fornecedor),
    historico: normalizar(r.historico),
    categoria: r.categoria,
  }),
)

export function categorizar(nomeFornecedor: string | null, historico: string | null): string {
  const fornNorm = normalizar(nomeFornecedor)
  const histNorm = normalizar(historico)
  for (const regra of REGRAS) {
    if (regra.fornecedor && !fornNorm.includes(regra.fornecedor)) continue
    if (regra.historico && !histNorm.includes(regra.historico)) continue
    return regra.categoria
  }
  return NAO_CLASSIFICADO
}
