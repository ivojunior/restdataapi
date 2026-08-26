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
