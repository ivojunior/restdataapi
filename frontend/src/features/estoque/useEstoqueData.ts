import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { buscarTodoEstoque, type FiltrosTipoEstoque } from './api'

/** Carrega o tipo/local do servidor (únicos filtros que vão para a API) e
 * aplica filial/código/descrição localmente sobre o resultado, sem nova
 * requisição — mesmo modelo de filtros de client/app_estoque.py
 * (_apply_filters). */
export function useEstoqueData(filtrosServidor: FiltrosTipoEstoque) {
  const [filial, setFilial] = useState('')
  const [codigo, setCodigo] = useState('')
  const [descricao, setDescricao] = useState('')

  const consulta = useQuery({
    queryKey: ['saldos-estoque', filtrosServidor.tipoProduto, filtrosServidor.local],
    queryFn: () => buscarTodoEstoque(filtrosServidor),
    staleTime: 5 * 60 * 1000,
  })

  const dadosBrutos = useMemo(() => consulta.data ?? [], [consulta.data])

  const dados = useMemo(() => {
    const filialAlvo = filial.trim()
    const codigoAlvo = codigo.trim().toLowerCase()
    const descricaoAlvo = descricao.trim().toLowerCase()
    if (!filialAlvo && !codigoAlvo && !descricaoAlvo) return dadosBrutos

    return dadosBrutos.filter((item) => {
      if (filialAlvo && item.filial !== filialAlvo) return false
      if (codigoAlvo && !item.codigo_produto.toLowerCase().includes(codigoAlvo)) return false
      if (descricaoAlvo && !(item.descricao_produto ?? '').toLowerCase().includes(descricaoAlvo)) {
        return false
      }
      return true
    })
  }, [dadosBrutos, filial, codigo, descricao])

  return {
    dados,
    dadosBrutos,
    filial,
    setFilial,
    codigo,
    setCodigo,
    descricao,
    setDescricao,
    isLoading: consulta.isLoading,
    isFetching: consulta.isFetching,
    isError: consulta.isError,
    error: consulta.error,
    refetch: consulta.refetch,
  }
}
