from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.domain.models import Import
from src.repositories.base import BaseRepository


class ImportRepository(BaseRepository[Import]):
    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_id(self, import_id: str) -> Import | None:
        return self.db.scalar(
            select(Import)
            .options(selectinload(Import.workouts), selectinload(Import.audit_events))
            .where(Import.id == import_id)
        )

    def get_by_sha256(self, sha256: str) -> Import | None:
        return self.db.scalar(select(Import).where(Import.sha256 == sha256))
