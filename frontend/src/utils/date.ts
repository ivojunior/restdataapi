/** (dataInicial, dataFinal) — primeiro e último dia do mês, formato
 * AAAAMMDD. Réplica de `_periodo_do_mes` em client/app_faturamento.py. */
export function periodoDoMes(ano: number, mes: number): { dataInicial: string; dataFinal: string } {
  const ultimoDia = new Date(ano, mes, 0).getDate()
  const pad = (n: number) => String(n).padStart(2, '0')
  return {
    dataInicial: `${ano}${pad(mes)}01`,
    dataFinal: `${ano}${pad(mes)}${pad(ultimoDia)}`,
  }
}

/** AAAAMMDD (formato da API) -> AAAA-MM-DD (formato esperado por
 * `<input type="date">`), e vice-versa. */
export function paraInputDate(aaaammdd: string): string {
  if (aaaammdd.length !== 8) return ''
  return `${aaaammdd.slice(0, 4)}-${aaaammdd.slice(4, 6)}-${aaaammdd.slice(6, 8)}`
}

export function deInputDate(valorInput: string): string {
  return valorInput.replaceAll('-', '')
}

/** AAAAMMDD -> hoje, no fuso local do browser. */
export function hojeAAAAMMDD(): string {
  const hoje = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${hoje.getFullYear()}${pad(hoje.getMonth() + 1)}${pad(hoje.getDate())}`
}

/** Diferença absoluta, em dias, entre uma data AAAAMMDD e hoje. NaN se a
 * data vier vazia/inválida (nunca "diferença enorme" por engano) — réplica
 * do `errors="coerce"` + `.abs()` em `_update_table` (client/app_cargas.py). */
export function diferencaEmDiasDeHoje(aaaammdd: string): number {
  if (aaaammdd.length !== 8 || !/^\d+$/.test(aaaammdd)) return NaN
  const ano = Number(aaaammdd.slice(0, 4))
  const mes = Number(aaaammdd.slice(4, 6))
  const dia = Number(aaaammdd.slice(6, 8))
  const data = new Date(ano, mes - 1, dia)
  const hoje = new Date()
  hoje.setHours(0, 0, 0, 0)
  const umDiaMs = 24 * 60 * 60 * 1000
  return Math.abs(Math.round((data.getTime() - hoje.getTime()) / umDiaMs))
}
