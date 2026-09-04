from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.models import ExerciseMapping
from src.repositories.base import BaseRepository


class ExerciseMappingRepository(BaseRepository[ExerciseMapping]):
    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_source_name(self, source_name: str) -> ExerciseMapping | None:
        return self.db.scalar(select(ExerciseMapping).where(ExerciseMapping.source_name == source_name))

    def get_confirmed(self) -> list[ExerciseMapping]:
        return list(self.db.scalars(select(ExerciseMapping).where(ExerciseMapping.confirmed_by_user.is_(True))))
