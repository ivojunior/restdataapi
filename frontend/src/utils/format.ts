// Réplica de _brl/_qtd/_pct em client/app_faturamento.py (e nos demais
// clients desktop), usando Intl em vez de f-strings + replace manual.

const FORMATADOR_BRL = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })
const FORMATADOR_QTD = new Intl.NumberFormat('pt-BR', {
  minimumFractionDigits: 2, maximumFractionDigits: 2,
})
const FORMATADOR_PCT = new Intl.NumberFormat('pt-BR', {
  minimumFractionDigits: 1, maximumFractionDigits: 1,
})

export function formatarBRL(valor: number): string {
  return Number.isFinite(valor) ? FORMATADOR_BRL.format(valor) : '—'
}

export function formatarQtd(valor: number): string {
  return Number.isFinite(valor) ? FORMATADOR_QTD.format(valor) : '—'
}

export function formatarPct(valor: number): string {
  return Number.isFinite(valor) ? `${FORMATADOR_PCT.format(valor)}%` : '—'
}

/** Converte um campo numérico da API (string) para number, tratando `null`
 * (razão não calculável, ex. margem de um grupo com faturamento zero — ver
 * FaturamentoItem) como NaN em vez de 0: `Number(null) === 0` em JS, o que
 * faria um valor "não calculável" aparecer como "0,0%" (parece zero, mas o
 * significado é outro) em vez de "—" via formatarBRL/formatarQtd/formatarPct. */
export function paraNumero(valor: string | null): number {
  return valor === null ? NaN : Number(valor)
}
