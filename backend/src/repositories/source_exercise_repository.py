from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.models import SourceExercise
from src.repositories.base import BaseRepository


class SourceExerciseRepository(BaseRepository[SourceExercise]):
    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_workout_id(self, workout_id: int) -> list[SourceExercise]:
        return list(
            self.db.scalars(
                select(SourceExercise).where(SourceExercise.workout_id == workout_id).order_by(SourceExercise.order)
            )
        )
