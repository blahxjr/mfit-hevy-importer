from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.models import Routine
from src.repositories.base import BaseRepository


class RoutineRepository(BaseRepository[Routine]):
    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_id(self, routine_id: str) -> Routine | None:
        return self.db.get(Routine, routine_id)

    def get_all(self) -> list[Routine]:
        return list(self.db.scalars(select(Routine).order_by(Routine.title)))
