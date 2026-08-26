// Campos numéricos chegam como string (Decimal do Pydantic serializado como
// texto — ver CargaRead em app/schemas/carga.py). motorista/nome_cliente/
// bairro_cliente/municipio_cliente são opcionais no schema (podem vir null).
export interface CargaItem {
  filial: string
  codigo: string
  data: string
  pedido: string
  motorista: string | null
  cliente: string
  nome_cliente: string | null
  bairro_cliente: string | null
  municipio_cliente: string | null
  peso: string
  nota_fiscal: string
  caminhao: string
  status_carga: string
  valor: string
}

export const STATUS_CARGA_FECHADO = 'Fechada'

/** Uma "carga" é identificada por (filial, codigo) — cada linha da API é um
 * ITEM de uma carga, não uma carga distinta (uma carga pode ter vários
 * pedidos/itens). Réplica de `_carga_key`/`_n_cargas` em client/app_cargas.py. */
export function chaveCarga(item: CargaItem): string {
  return `${item.filial}-${item.codigo}`
}
