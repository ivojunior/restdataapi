// Campos numéricos chegam como string (Decimal do Pydantic serializado como
// texto — ver FinanceiroRead em app/schemas/financeiro.py). Vários campos
// são opcionais no schema (podem vir null: sem join correspondente, ou
// campo vazio no cadastro do Protheus).
export interface FinanceiroItem {
  filial: string
  numero: string
  parcela: string
  tipo: string
  codigo_operacao: string | null
  descricao_operacao: string | null
  valor: string
  saldo: string
  emissao: string
  vencimento_real: string
  nome_fornecedor: string | null
  data_baixa: string | null
  historico: string
  recuperacao_judicial: string | null
}

export type StatusFinanceiro = 'Em aberto' | 'Vencido' | 'Baixado'

export const STATUS_CORES: Record<StatusFinanceiro, string> = {
  'Em aberto': '#27ae60',
  Vencido: '#e74c3c',
  Baixado: '#95a5a6',
}

/** FinanceiroItem + os campos que a API não expõe (calculados no cliente,
 * réplica de _status_from_row/_mes_ano/categorias.classify em
 * client/app_financeiro.py). */
export interface FinanceiroItemEnriquecido extends FinanceiroItem {
  status: StatusFinanceiro
  mesAno: string // AAAAMM, chave ordenável; '' se vencimento_real for inválido
  categoria: string
}
