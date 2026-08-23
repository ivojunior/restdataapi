from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class CRUDBase(Generic[ModelType]):
    """Operações de leitura reutilizáveis para modelos SQLAlchemy simples (API somente leitura)."""

    def __init__(self, model: Type[ModelType], pk_field: str = "id"):
        self.model = model
        self.pk_field = pk_field

    def _base_query(self, db: Session):
        """Ponto de extensão para subclasses aplicarem filtros sempre presentes
        (ex.: exclusão lógica de tabelas legadas)."""
        return db.query(self.model)

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        return self._base_query(db).filter(getattr(self.model, self.pk_field) == id).first()

    def list(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 50,
        order_by: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[ModelType]:
        query = self._base_query(db)

        for field, value in (filters or {}).items():
            query = query.filter(getattr(self.model, field) == value)

        column = None
        if order_by:
            column = getattr(self.model, order_by.lstrip("-"), None)
        descending = bool(order_by) and order_by.startswith("-")
        if column is None:
            # MSSQL exige ORDER BY sempre que a query usa OFFSET/LIMIT.
            column = getattr(self.model, self.pk_field)
            descending = False
        query = query.order_by(desc(column) if descending else asc(column))

        return query.offset(skip).limit(limit).all()
