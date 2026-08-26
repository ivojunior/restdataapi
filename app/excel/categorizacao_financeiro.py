"""Categorização de títulos do relatório financeiro para a exportação Excel
(GET /financeiro/export) — réplica de client/categorias.py, mas lendo as
regras de app/excel/data/categorias_financeiro.json (cópia estática
extraída de client/categorias.xlsx) em vez de um .xlsx editável.

A categoria não é uma coluna de nenhuma tabela do Protheus mapeada por este
projeto — GET /financeiro/ nunca a expõe; quem categoriza os dados exibidos
na tela da SPA é o próprio frontend (mesma lógica duplicada em
frontend/src/features/financeiro/categorizacao.ts, a partir do mesmo JSON
copiado de client/categorias.xlsx). Risco assumido: as duas cópias podem
divergir se alguém editar categorias.xlsx sem atualizar as duas cópias — não
há hoje um mecanismo automático que as mantenha sincronizadas.
"""
import json
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import List

_REGRAS_PATH = Path(__file__).parent / "data" / "categorias_financeiro.json"
NAO_CLASSIFICADO = "Não Classificado"


@dataclass
class _Regra:
    fornecedor: str
    historico: str
    categoria: str


def _normalizar(s) -> str:
    s = unicodedata.normalize("NFD", str(s or ""))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.strip().lower()


def _carregar_regras() -> List[_Regra]:
    with open(_REGRAS_PATH, encoding="utf-8") as f:
        bruto = json.load(f)
    return [
        _Regra(
            fornecedor=_normalizar(r["fornecedor"]),
            historico=_normalizar(r["historico"]),
            categoria=r["categoria"],
        )
        for r in bruto
    ]


# Carregadas uma vez, no import do módulo — o arquivo não muda em tempo de
# execução (é um artefato de build, não editável pelo usuário via SPA).
_REGRAS = _carregar_regras()


def categorizar(nome_fornecedor, historico) -> str:
    forn_norm = _normalizar(nome_fornecedor)
    hist_norm = _normalizar(historico)
    for regra in _REGRAS:
        if regra.fornecedor and regra.fornecedor not in forn_norm:
            continue
        if regra.historico and regra.historico not in hist_norm:
            continue
        return regra.categoria
    return NAO_CLASSIFICADO
