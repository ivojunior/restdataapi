from typing import Any, Dict, Generic, List, Optional, Tuple, Type, TypeVar

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
    ) -> Tuple[List[ModelType], int]:
        query = self._base_query(db)

        for field, value in (filters or {}).items():
            query = query.filter(getattr(self.model, field) == value)

        if order_by:
            column_name = order_by.lstrip("-")
            column = getattr(self.model, column_name, None)
            if column is not None:
                query = query.order_by(desc(column) if order_by.startswith("-") else asc(column))

        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total
