from typing import Optional

from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, Query

from app.crud.base import CRUDBase
from app.database import get_db
from app.models.titulo_pagar import TituloPagar
from app.schemas.common import PaginatedResponse
from app.schemas.titulo_pagar import TituloPagarRead
from app.security import verify_api_key_or_session

router = APIRouter(
    prefix="/titulos-pagar",
    tags=["Títulos a Pagar"],
    dependencies=[Depends(verify_api_key_or_session)],
)


class CRUDTituloPagar(CRUDBase):
    def _base_query(self, db: Session):
        # Convenção Protheus: registros com D_E_L_E_T_ = '*' estão logicamente excluídos.
        return db.query(self.model).filter(self.model.deletado != "*")


crud_titulo_pagar = CRUDTituloPagar(TituloPagar, pk_field="rec_no")


@router.get("/", response_model=PaginatedResponse[TituloPagarRead])
def listar_titulos_pagar(
    skip: int = 0,
    limit: int = Query(50, le=200),
    order_by: Optional[str] = None,
    filial: Optional[str] = None,
    fornecedor: Optional[str] = None,
    prefixo: Optional[str] = None,
    numero: Optional[str] = None,
    db: Session = Depends(get_db),
):
    filters = {}
    if filial:
        filters["filial"] = filial
    if fornecedor:
        filters["fornecedor"] = fornecedor
    if prefixo:
        filters["prefixo"] = prefixo
    if numero:
        filters["numero"] = numero
    items = crud_titulo_pagar.list(db, skip, limit, order_by, filters)
    return {"skip": skip, "limit": limit, "items": items}


@router.get("/{rec_no}", response_model=TituloPagarRead)
def obter_titulo_pagar(rec_no: int, db: Session = Depends(get_db)):
    titulo = crud_titulo_pagar.get(db, rec_no)
    if not titulo:
        raise HTTPException(404, "Título a pagar não encontrado")
    return titulo
