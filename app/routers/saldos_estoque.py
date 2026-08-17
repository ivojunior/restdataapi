from typing import Optional

from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, Query

from app.crud.base import CRUDBase
from app.database import get_db
from app.models.saldo_estoque import SaldoEstoque
from app.schemas.common import PaginatedResponse
from app.schemas.saldo_estoque import SaldoEstoqueRead
from app.security import verify_api_key

router = APIRouter(
    prefix="/saldos-estoque",
    tags=["Saldo de Estoque"],
    dependencies=[Depends(verify_api_key)],
)


class CRUDSaldoEstoque(CRUDBase):
    def _base_query(self, db: Session):
        # Convenção Protheus: registros com D_E_L_E_T_ = '*' estão logicamente excluídos.
        return db.query(self.model).filter(self.model.deletado != "*")


crud_saldo_estoque = CRUDSaldoEstoque(SaldoEstoque, pk_field="rec_no")


@router.get("/", response_model=PaginatedResponse[SaldoEstoqueRead])
def listar_saldos_estoque(
    skip: int = 0,
    limit: int = Query(50, le=200),
    order_by: Optional[str] = None,
    filial: Optional[str] = None,
    codigo_produto: Optional[str] = None,
    local: Optional[str] = None,
    db: Session = Depends(get_db),
):
    filters = {}
    if filial:
        filters["filial"] = filial
    if codigo_produto:
        filters["codigo_produto"] = codigo_produto
    if local:
        filters["local"] = local
    items, total = crud_saldo_estoque.list(db, skip, limit, order_by, filters)
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.get("/{rec_no}", response_model=SaldoEstoqueRead)
def obter_saldo_estoque(rec_no: int, db: Session = Depends(get_db)):
    saldo = crud_saldo_estoque.get(db, rec_no)
    if not saldo:
        raise HTTPException(404, "Saldo de estoque não encontrado")
    return saldo
