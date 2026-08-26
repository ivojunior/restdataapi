// Campos numéricos chegam como string — a API serializa Decimal do Pydantic
// como texto (ver FaturamentoRead em app/schemas/faturamento.py), não como
// number JSON, para não perder precisão. Converter com Number(...) ao usar.
export interface FaturamentoItem {
  filial: string
  dia: number
  codigo: string
  descricao: string
  quantidade: string
  // null quando o denominador da razão é zero para este grupo (ex.: só
  // bonificação, sem venda, no mesmo filial/dia/produto) — "não é possível
  // calcular", não "zero". Ver o comentário sobre func.nullif em
  // app/routers/faturamento.py.
  preco_medio: string | null
  faturamento: string
  custo: string
  lucro_bruto: string
  margem: string | null
  markup: string | null
}
