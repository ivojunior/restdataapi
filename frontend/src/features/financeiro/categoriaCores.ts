import { CORES_GRAFICO } from '../../components/charts/colors'
import { CATEGORIAS_CANONICAS, NAO_CLASSIFICADO } from './categorizacao'

/** categoria -> cor fixa, réplica de `CATEGORIA_COLORS` (dict(zip(...)))
 * em client/app_financeiro.py. */
const MAPA: Record<string, string> = Object.fromEntries(
  CATEGORIAS_CANONICAS.map((categoria, i) => [categoria, CORES_GRAFICO[i % CORES_GRAFICO.length]]),
)

export function corDaCategoria(categoria: string | number): string {
  if (categoria === NAO_CLASSIFICADO) return '#7f8c8d'
  return MAPA[String(categoria)] ?? '#7f8c8d'
}
