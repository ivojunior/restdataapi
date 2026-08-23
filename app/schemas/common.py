from typing import Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    # Sem "total": um count(*) exato sobre os mesmos JOINs/filtros da listagem
    # não pode parar cedo como o SELECT paginado (que usa ORDER BY + OFFSET/
    # FETCH e para assim que preenche a página) — precisa avaliar todas as
    # linhas que casam nos joins até o fim. Em tabelas grandes do Protheus
    # isso levava o count sozinho a >45s mesmo com a página respondendo em
    # ~1s. Nenhum client atual depende de "total": todos paginam em loop até
    # receber uma página vazia (skip/limit continuam existindo para isso).
    skip: int
    limit: int
    items: List[T]
