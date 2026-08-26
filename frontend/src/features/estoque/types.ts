// Campos numéricos chegam como string (Decimal do Pydantic serializado como
// texto — ver SaldoEstoqueRead em app/schemas/saldo_estoque.py). descricao_produto
// e valor_atual são opcionais no schema (podem vir null).
export interface EstoqueItem {
  filial: string
  local: string
  codigo_produto: string
  descricao_produto: string | null
  quantidade: string
  valor_atual: string | null
}
