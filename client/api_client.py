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

    def get_financeiro_page(self, skip: int = 0, limit: int = 200) -> Dict:
        return self._get("/financeiro/", {"skip": skip, "limit": limit})

    def get_all_financeiro(
        self,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Tuple[List[Dict], int]:
        """Busca todas as páginas do relatório financeiro.

        O endpoint /financeiro não aceita filtros de query string — os filtros
        de negócio (vencimento mínimo e tipos excluídos) já vêm fixos do servidor;
        qualquer filtro adicional (filial, fornecedor, tipo etc.) é aplicado no
        cliente, após o carregamento completo dos dados.
        """
        all_items: List[Dict] = []
        skip = 0
        limit = 200

        while True:
            result = self.get_financeiro_page(skip=skip, limit=limit)
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
