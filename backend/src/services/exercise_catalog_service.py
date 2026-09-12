"""Casos de uso do catálogo de exercícios."""

from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.models import Exercise, ExerciseTemplate
from src.exercise_db.client import ExerciseDbClient
from src.repositories.exercise_repository import ExerciseRepository, normalize_name


class ExerciseCatalogService:
    def __init__(self, db: Session, client: ExerciseDbClient | None = None) -> None:
        self.db, self.client = db, client
        self.repo = ExerciseRepository(db)

    def sync_from_exercise_db(self, *, max_pages: int = 100, limit: int = 100) -> dict[str, int | list[str]]:
        own_client = self.client is None
        client = self.client or ExerciseDbClient()
        created = updated = 0
        errors: list[str] = []
        try:
            for page in range(1, max_pages + 1):
                items = client.list_exercises(page, limit)
                if not items:
                    break
                for item in items:
                    existed = self.repo.get_by_exercisedb_id(item.external_id) is not None
                    self.repo.upsert_from_exercisedb(item)
                    updated += 1
                    created += int(not existed)
                self.db.commit()
                if len(items) < limit:
                    break
        except Exception as exc:
            self.db.rollback()
            errors.append(str(exc))
        finally:
            if own_client:
                client.close()
        return {"created": created, "updated": updated, "pages": page if 'page' in locals() else 0, "errors": errors}

    def enrich_with_hevy_templates(self, threshold: float = 0.82) -> dict[str, int]:
        templates = list(self.db.scalars(select(ExerciseTemplate)))
        linked = 0
        for exercise in self.db.scalars(select(Exercise).where(Exercise.hevy_template_id.is_(None))):
            candidates = [(fuzz.WRatio(normalize_name(exercise.name), normalize_name(template.title)) / 100, template) for template in templates]
            if candidates:
                score, template = max(candidates, key=lambda item: item[0])
                if score >= threshold:
                    exercise.hevy_template_id = template.id
                    linked += 1
        self.db.commit()
        return {"linked": linked, "candidates": len(templates)}