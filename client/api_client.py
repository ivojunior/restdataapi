"""Cliente HTTP para a RestDataAPI."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

import requests


class APIClient:
    def __init__(self, base_url: str, api_key: str, api_key_name: str = "X-API-Key") -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = {api_key_name: api_key}
        self.timeout = 30

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict:
        resp = requests.get(
            f"{self.base_url}{path}",
            params=params or {},
            headers=self.headers,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def health(self) -> Dict:
        return self._get("/health")

    def get_financeiro_page(
        self,
        skip: int = 0,
        limit: int = 200,
        vencimento_de: Optional[str] = None,
        vencimento_ate: Optional[str] = None,
    ) -> Dict:
        params: Dict[str, Any] = {"skip": skip, "limit": limit}
        if vencimento_de:
            params["vencimento_de"] = vencimento_de
        if vencimento_ate:
            params["vencimento_ate"] = vencimento_ate
        return self._get("/financeiro/", params)

    def get_all_financeiro(
        self,
        vencimento_de: Optional[str] = None,
        vencimento_ate: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Tuple[List[Dict], int]:
        """Busca todas as páginas do relatório financeiro.

        O endpoint /financeiro exclui sempre os tipos de título PA/PR/NDF
        (regra fixa). O período (vencimento_de/vencimento_ate) é
        parametrizável — sem vencimento_de, a API assume a data atual do
        sistema; sem vencimento_ate, não há limite superior. Qualquer outro
        filtro (filial, fornecedor, tipo etc.) é aplicado no cliente, após o
        carregamento completo dos dados.
        """
        all_items: List[Dict] = []
        skip = 0
        limit = 200

        while True:
            result = self.get_financeiro_page(
                skip=skip, limit=limit,
                vencimento_de=vencimento_de, vencimento_ate=vencimento_ate)
            items = result["items"]
            total = result["total"]
            all_items.extend(items)
            skip += len(items)

            if progress_callback:
                progress_callback(len(all_items), total)

            if skip >= total or not items:
                break

        return all_items, total

    def get_cargas_page(
        self,
        skip: int = 0,
        limit: int = 200,
        data_inicial: Optional[str] = None,
    ) -> Dict:
        params: Dict[str, Any] = {"skip": skip, "limit": limit}
        if data_inicial:
            params["data_inicial"] = data_inicial
        return self._get("/cargas/", params)

    def get_all_cargas(
        self,
        data_inicial: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Tuple[List[Dict], int]:
        """Busca todas as páginas do relatório de cargas.

        O endpoint /cargas aplica sempre como regra fixa apenas itens não
        excluídos e não cancelados; a data mínima (data_inicial) é
        parametrizável — é o cliente quem decide a partir de qual data
        consultar. Sem o parâmetro, a API traz cargas de qualquer data.
        Qualquer outro filtro (filial, cliente, caminhão etc.) é aplicado no
        cliente, após o carregamento completo dos dados.
        """
        all_items: List[Dict] = []
        skip = 0
        limit = 200

        while True:
            result = self.get_cargas_page(skip=skip, limit=limit, data_inicial=data_inicial)
            items = result["items"]
            total = result["total"]
            all_items.extend(items)
            skip += len(items)

            if progress_callback:
                progress_callback(len(all_items), total)

            if skip >= total or not items:
                break

        return all_items, total

    def get_saldos_estoque_page(
        self,
        skip: int = 0,
        limit: int = 200,
        tipo_produto: Optional[str] = None,
        local: Optional[str] = None,
    ) -> Dict:
        params: Dict[str, Any] = {"skip": skip, "limit": limit}
        if tipo_produto:
            params["tipo_produto"] = tipo_produto
        if local:
            params["local"] = local
        return self._get("/saldos-estoque/", params)

    def get_all_saldos_estoque(
        self,
        tipo_produto: Optional[str] = None,
        local: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Tuple[List[Dict], int]:
        """Busca todas as páginas do relatório de saldo de estoque.

        O endpoint /saldos-estoque aplica sempre como regra fixa apenas saldo
        positivo e registros não excluídos; tipo de produto e armazém são
        parametrizáveis (tipo_produto/local) — é o cliente quem decide qual
        recorte de estoque consultar. Qualquer outro filtro (filial, código,
        descrição etc.) é aplicado no cliente, após o carregamento completo
        dos dados.
        """
        all_items: List[Dict] = []
        skip = 0
        limit = 200

        while True:
            result = self.get_saldos_estoque_page(
                skip=skip, limit=limit, tipo_produto=tipo_produto, local=local)
            items = result["items"]
            total = result["total"]
            all_items.extend(items)
            skip += len(items)

            if progress_callback:
                progress_callback(len(all_items), total)

            if skip >= total or not items:
                break

        return all_items, total
