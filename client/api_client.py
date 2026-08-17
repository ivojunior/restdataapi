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

    def get_titulos_pagar_page(
        self,
        skip: int = 0,
        limit: int = 200,
        filial: Optional[str] = None,
        fornecedor: Optional[str] = None,
        prefixo: Optional[str] = None,
        numero: Optional[str] = None,
    ) -> Dict:
        params: Dict[str, Any] = {"skip": skip, "limit": limit}
        if filial:
            params["filial"] = filial
        if fornecedor:
            params["fornecedor"] = fornecedor
        if prefixo:
            params["prefixo"] = prefixo
        if numero:
            params["numero"] = numero
        return self._get("/titulos-pagar/", params)

    def get_all_titulos_pagar(
        self,
        filial: Optional[str] = None,
        fornecedor: Optional[str] = None,
        prefixo: Optional[str] = None,
        numero: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Tuple[List[Dict], int]:
        all_items: List[Dict] = []
        skip = 0
        limit = 200

        while True:
            result = self.get_titulos_pagar_page(
                skip=skip, limit=limit,
                filial=filial, fornecedor=fornecedor,
                prefixo=prefixo, numero=numero,
            )
            items = result["items"]
            total = result["total"]
            all_items.extend(items)
            skip += len(items)

            if progress_callback:
                progress_callback(len(all_items), total)

            if skip >= total or not items:
                break

        return all_items, total
