from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.models import NormalizedExercise, SourceExercise, SourceWorkout
from src.parsers.workout_normalizer import WorkoutNormalizer
from src.repositories.import_repository import ImportRepository


class WorkoutNormalizerAgent:
    def __init__(self, db: Session):
        self.db, self.normalizer, self.import_repo = db, WorkoutNormalizer(), ImportRepository(db)

    def normalize_import(self, import_id: str):
        if not self.import_repo.get_by_id(import_id):
            return {
                "import_id": import_id,
                "error": "Import not found",
                "normalized_count": 0,
                "needs_review_count": 0,
                "warnings": [],
            }
        sources = self.db.scalars(
            select(SourceExercise).join(SourceWorkout).where(SourceWorkout.import_id == import_id)
        ).all()
        reviews = 0
        for source in sources:
            parsed = self.normalizer.normalize_sets_reps(source.sets_raw, source.reps_raw)
            load, unit, lr, lrn = self.normalizer.normalize_load(source.load_raw)
            rest, rr, rrn = self.normalizer.normalize_rest(source.rest_raw)
            reasons = [x for x in (parsed.review_reason, lrn, rrn) if x]
            normalized = source.normalized or NormalizedExercise(source_exercise=source)
            self.db.add(normalized)
            normalized.sets_min, normalized.sets_max, normalized.reps_min, normalized.reps_max = (
                parsed.sets_min,
                parsed.sets_max,
                parsed.reps_min,
                parsed.reps_max,
            )
            normalized.load_value, normalized.load_unit, normalized.rest_seconds = load, unit, rest
            normalized.is_timed, normalized.duration_seconds = parsed.is_timed, parsed.duration_seconds
            normalized.sets_raw, normalized.reps_raw, normalized.load_raw, normalized.rest_raw = (
                source.sets_raw,
                source.reps_raw,
                source.load_raw,
                source.rest_raw,
            )
            normalized.needs_review = parsed.needs_review or lr or rr
            normalized.review_reason = "; ".join(reasons) or None
            normalized.confidence = parsed.confidence * (0 if lr or rr else 1)
            reviews += normalized.needs_review
        self.db.commit()
        return {"import_id": import_id, "normalized_count": len(sources), "needs_review_count": reviews, "warnings": []}
