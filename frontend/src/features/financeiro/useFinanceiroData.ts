import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { buscarTodoFinanceiro, type FiltrosServidorFinanceiro } from './api'
import { enriquecerItens } from './enriquecimento'

/** Carrega o período/status do servidor e aplica filial/fornecedor/tipo/
 * tipo de operação/categoria localmente sobre o resultado (já enriquecido
 * com status/categoria/mesAno) — mesmo modelo de filtros de
 * client/app_financeiro.py (_apply_filters); o período de vencimento já
 * foi filtrado no servidor, não é reaplicado aqui. */
export function useFinanceiroData(filtrosServidor: FiltrosServidorFinanceiro) {
  const [filial, setFilial] = useState('')
  const [fornecedor, setFornecedor] = useState('')
  const [tipo, setTipo] = useState('')
  const [tipoOperacao, setTipoOperacao] = useState('')
  const [categoria, setCategoria] = useState('')

  const consulta = useQuery({
    queryKey: [
      'financeiro', filtrosServidor.vencimentoDe, filtrosServidor.vencimentoAte,
      filtrosServidor.status,
    ],
    queryFn: () => buscarTodoFinanceiro(filtrosServidor),
    staleTime: 5 * 60 * 1000,
  })

  const dadosBrutos = useMemo(
    () => enriquecerItens(consulta.data ?? []),
    [consulta.data],
  )

  const dados = useMemo(() => {
    const filialAlvo = filial.trim()
    const fornecedorAlvo = fornecedor.trim().toLowerCase()
    const tipoAlvo = tipo.trim().toUpperCase()
    const tipoOperacaoAlvo = tipoOperacao.trim().toLowerCase()
    const categoriaAlvo = categoria.trim()

    return dadosBrutos.filter((item) => {
      if (filialAlvo && item.filial !== filialAlvo) return false
      if (fornecedorAlvo && !(item.nome_fornecedor ?? '').toLowerCase().includes(fornecedorAlvo)) {
        return false
      }
      if (tipoAlvo && (item.tipo ?? '').toUpperCase() !== tipoAlvo) return false
      if (
        tipoOperacaoAlvo &&
        !(item.descricao_operacao ?? '').toLowerCase().includes(tipoOperacaoAlvo)
      ) {
        return false
      }
      if (categoriaAlvo && item.categoria !== categoriaAlvo) return false
      return true
    })
  }, [dadosBrutos, filial, fornecedor, tipo, tipoOperacao, categoria])

  return {
    dados,
    dadosBrutos,
    filial, setFilial,
    fornecedor, setFornecedor,
    tipo, setTipo,
    tipoOperacao, setTipoOperacao,
    categoria, setCategoria,
    isLoading: consulta.isLoading,
    isFetching: consulta.isFetching,
    isError: consulta.isError,
    error: consulta.error,
    refetch: consulta.refetch,
  }
}
