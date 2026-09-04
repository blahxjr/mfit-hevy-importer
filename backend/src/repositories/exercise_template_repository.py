from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.models import ExerciseTemplate
from src.repositories.base import BaseRepository


class ExerciseTemplateRepository(BaseRepository[ExerciseTemplate]):
    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_id(self, template_id: str) -> ExerciseTemplate | None:
        return self.db.get(ExerciseTemplate, template_id)

    def get_all(self) -> list[ExerciseTemplate]:
        return list(self.db.scalars(select(ExerciseTemplate).order_by(ExerciseTemplate.title)))

    def get_by_title(self, title: str) -> ExerciseTemplate | None:
        return self.db.scalar(select(ExerciseTemplate).where(ExerciseTemplate.title == title))
