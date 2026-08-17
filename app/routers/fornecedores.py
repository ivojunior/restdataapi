from typing import Optional

from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, Query

from app.crud.base import CRUDBase
from app.database import get_db
from app.models.fornecedor import Fornecedor
from app.schemas.common import PaginatedResponse
from app.schemas.fornecedor import FornecedorRead
from app.security import verify_api_key

router = APIRouter(
    prefix="/fornecedores",
    tags=["Fornecedores"],
    dependencies=[Depends(verify_api_key)],
)


class CRUDFornecedor(CRUDBase):
    def _base_query(self, db: Session):
        # Convenção Protheus: registros com D_E_L_E_T_ = '*' estão logicamente excluídos.
        return db.query(self.model).filter(self.model.deletado != "*")


crud_fornecedor = CRUDFornecedor(Fornecedor, pk_field="rec_no")


@router.get("/", response_model=PaginatedResponse[FornecedorRead])
def listar_fornecedores(
    skip: int = 0,
    limit: int = Query(50, le=200),
    order_by: Optional[str] = None,
    filial: Optional[str] = None,
    codigo: Optional[str] = None,
    cnpj_cpf: Optional[str] = None,
    nome: Optional[str] = None,
    db: Session = Depends(get_db),
):
    filters = {}
    if filial:
        filters["filial"] = filial
    if codigo:
        filters["codigo"] = codigo
    if cnpj_cpf:
        filters["cnpj_cpf"] = cnpj_cpf
    if nome:
        filters["nome"] = nome
    items, total = crud_fornecedor.list(db, skip, limit, order_by, filters)
    return {"total": total, "skip": skip, "limit": limit, "items": items}


@router.get("/{rec_no}", response_model=FornecedorRead)
def obter_fornecedor(rec_no: int, db: Session = Depends(get_db)):
    fornecedor = crud_fornecedor.get(db, rec_no)
    if not fornecedor:
        raise HTTPException(404, "Fornecedor não encontrado")
    return fornecedor
