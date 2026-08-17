from typing import Optional

from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, Query

from app.crud.base import CRUDBase
from app.database import get_db
from app.models.produto import Produto
from app.schemas.common import PaginatedResponse
from app.schemas.produto import ProdutoRead
from app.security import verify_api_key

router = APIRouter(
    prefix="/produtos",
    tags=["Produtos"],
    dependencies=[Depends(verify_api_key)],
)


class CRUDProduto(CRUDBase):
    def _base_query(self, db: Session):
        # Convenção Protheus: registros com D_E_L_E_T_ = '*' estão logicamente excluídos.
        return db.query(self.model).filter(self.model.deletado != "*")


crud_produto = CRUDProduto(Produto, pk_field="rec_no")


@router.get("/", response_model=PaginatedResponse[ProdutoRead])
def listar_produtos(
    skip: int = 0,
    limit: int = Query(50, le=200),
    order_by: Optional[str] = None,
    filial: Optional[str] = None,
    codigo: Optional[str] = None,
    grupo: Optional[str] = None,
    db: Session = Depends(get_db),
):
    filters = {}
    if filial:
        filters["filial"] = filial
    if codigo:
        filters["codigo"] = codigo
    if grupo:
        filters["grupo"] = grupo
    items, total = crud_produto.list(db, skip, limit, order_by, filters)
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.get("/{rec_no}", response_model=ProdutoRead)
def obter_produto(rec_no: int, db: Session = Depends(get_db)):
    produto = crud_produto.get(db, rec_no)
    if not produto:
        raise HTTPException(404, "Produto não encontrado")
    return produto
