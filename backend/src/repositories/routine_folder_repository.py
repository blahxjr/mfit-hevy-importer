from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.models import RoutineFolder
from src.repositories.base import BaseRepository


class RoutineFolderRepository(BaseRepository[RoutineFolder]):
    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_id(self, folder_id: int) -> RoutineFolder | None:
        return self.db.get(RoutineFolder, folder_id)

    def get_all(self) -> list[RoutineFolder]:
        return list(self.db.scalars(select(RoutineFolder).order_by(RoutineFolder.index)))
