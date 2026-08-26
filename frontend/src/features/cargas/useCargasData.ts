import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { buscarTodasCargas, type FiltrosServidorCargas } from './api'

/** Carrega o período/status do servidor e aplica filial/cliente/caminhão
 * localmente sobre o resultado, sem nova requisição — mesmo modelo de
 * filtros de client/app_cargas.py (_apply_filters). */
export function useCargasData(filtrosServidor: FiltrosServidorCargas) {
  const [filial, setFilial] = useState('')
  const [cliente, setCliente] = useState('')
  const [caminhao, setCaminhao] = useState('')

  const consulta = useQuery({
    queryKey: ['cargas', filtrosServidor.dataInicial, filtrosServidor.dataFinal, filtrosServidor.status],
    queryFn: () => buscarTodasCargas(filtrosServidor),
    staleTime: 5 * 60 * 1000,
  })

  const dadosBrutos = useMemo(() => consulta.data ?? [], [consulta.data])

  const dados = useMemo(() => {
    const filialAlvo = filial.trim()
    const clienteAlvo = cliente.trim().toLowerCase()
    const caminhaoAlvo = caminhao.trim().toLowerCase()
    if (!filialAlvo && !clienteAlvo && !caminhaoAlvo) return dadosBrutos

    return dadosBrutos.filter((item) => {
      if (filialAlvo && item.filial !== filialAlvo) return false
      if (clienteAlvo && !(item.nome_cliente ?? '').toLowerCase().includes(clienteAlvo)) return false
      if (caminhaoAlvo && !item.caminhao.toLowerCase().includes(caminhaoAlvo)) return false
      return true
    })
  }, [dadosBrutos, filial, cliente, caminhao])

  return {
    dados,
    dadosBrutos,
    filial,
    setFilial,
    cliente,
    setCliente,
    caminhao,
    setCaminhao,
    isLoading: consulta.isLoading,
    isFetching: consulta.isFetching,
    isError: consulta.isError,
    error: consulta.error,
    refetch: consulta.refetch,
  }
}
