import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { buscarTodoFaturamento, type FiltrosPeriodo } from './api'

/** Carrega o período do servidor (dataInicial/dataFinal — únicos filtros que
 * vão para a API) e aplica filial/produto localmente sobre o resultado, sem
 * nova requisição — mesmo modelo de filtros de client/app_faturamento.py
 * (_apply_filters): tudo que não é o período é filtro local. */
export function useFaturamentoData(periodo: FiltrosPeriodo) {
  const [filial, setFilial] = useState('')
  const [produto, setProduto] = useState('')

  const consulta = useQuery({
    queryKey: ['faturamento', periodo.dataInicial, periodo.dataFinal],
    queryFn: () => buscarTodoFaturamento(periodo),
    staleTime: 5 * 60 * 1000,
  })

  const dadosBrutos = useMemo(() => consulta.data ?? [], [consulta.data])

  const dados = useMemo(() => {
    const filialAlvo = filial.trim()
    const produtoAlvo = produto.trim().toLowerCase()
    if (!filialAlvo && !produtoAlvo) return dadosBrutos

    return dadosBrutos.filter((item) => {
      if (filialAlvo && item.filial !== filialAlvo) return false
      if (
        produtoAlvo &&
        !item.codigo.toLowerCase().includes(produtoAlvo) &&
        !(item.descricao ?? '').toLowerCase().includes(produtoAlvo)
      ) {
        return false
      }
      return true
    })
  }, [dadosBrutos, filial, produto])

  return {
    dados,
    dadosBrutos,
    filial,
    setFilial,
    produto,
    setProduto,
    isLoading: consulta.isLoading,
    isFetching: consulta.isFetching,
    isError: consulta.isError,
    error: consulta.error,
    refetch: consulta.refetch,
  }
}
