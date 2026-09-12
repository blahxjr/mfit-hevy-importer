"""Orquestração do catálogo próprio para a API."""

from sqlalchemy.orm import Session

from src.exercise_db.client import ExerciseDbClient
from src.repositories.exercise_repository import ExerciseRepository
from src.services.exercise_catalog_service import ExerciseCatalogService


class ExerciseCatalogAgent:
    def __init__(self, db: Session, client: ExerciseDbClient | None = None) -> None:
        self.db = db
        self.service = ExerciseCatalogService(db, client)
        self.repo = ExerciseRepository(db)

    def sync(self) -> dict[str, object]:
        result = self.service.sync_from_exercise_db()
        result["enrichment"] = self.service.enrich_with_hevy_templates()
        return result

    def list(self, **filters: object):
        return self.repo.search(**filters)

    def get(self, exercise_id: str):
        return self.repo.get_by_id(exercise_id)