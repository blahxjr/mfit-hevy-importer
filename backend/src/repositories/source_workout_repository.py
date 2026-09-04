from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.models import SourceWorkout
from src.repositories.base import BaseRepository


class SourceWorkoutRepository(BaseRepository[SourceWorkout]):
    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_import_id(self, import_id: str) -> list[SourceWorkout]:
        return list(
            self.db.scalars(
                select(SourceWorkout).where(SourceWorkout.import_id == import_id).order_by(SourceWorkout.order)
            )
        )
