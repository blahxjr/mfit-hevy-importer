"""Constrói operações de escrita no Hevy sem executá-las."""

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.domain.models import ExerciseMapping, NormalizedExercise, SourceExercise, SourceWorkout
from src.repositories.import_repository import ImportRepository


class PayloadBuilderAgent:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.import_repo = ImportRepository(db)

    def build_payload(self, import_id: str, folder_id: int | None = None, workout_order: int | None = None) -> dict:
        imported = self.import_repo.get_by_id(import_id)
        if not imported:
            return {
                "import_id": import_id,
                "error": "Import not found",
                "operations": [],
                "blocked": True,
                "warnings": [],
            }
        if workout_order is None:
            return {
                "import_id": import_id,
                "error": "workout_order is required",
                "operations": [],
                "blocked": True,
                "warnings": ["Select exactly one approved workout before building payload"],
            }
        mappings = {row.source_name: row for row in self.db.scalars(select(ExerciseMapping)).all()}
        workouts = self.db.scalars(
            select(SourceWorkout)
            .options(selectinload(SourceWorkout.exercises))
            .where(SourceWorkout.import_id == import_id)
            .order_by(SourceWorkout.order)
        ).all()
        workouts = [workout for workout in workouts if workout.order == workout_order]
        if not workouts:
            return {
                "import_id": import_id,
                "error": f"Workout order {workout_order} not found",
                "operations": [],
                "blocked": True,
                "warnings": [],
            }
        if workouts[0].status != "approved":
            return {
                "import_id": import_id,
                "error": "Workout not approved",
                "operations": [],
                "blocked": True,
                "warnings": ["Workout must be approved before building payload"],
            }
        operations, warnings, blocked = [], [], False
        for workout in workouts:
            exercises, errors = [], []
            for source in sorted(workout.exercises, key=lambda row: row.order):
                mapping = mappings.get(source.source_name)
                normalized = source.normalized
                if not mapping or not mapping.template_id or not mapping.confirmed_by_user:
                    errors.append(f"Unconfirmed mapping for {source.source_name}")
                    continue
                if not normalized or normalized.needs_review:
                    errors.append(f"Normalization needs review for {source.source_name}")
                    continue
                exercises.append(self._exercise_payload(source, normalized, mapping.template_id))
            if errors:
                blocked = True
                warnings.extend(errors)
            payload = {
                "title": f"{workout.source_name} (MFIT Import {date.today().isoformat()})",
                "exercises": exercises,
            }
            if folder_id is not None:
                payload["folder_id"] = folder_id
            operations.append(
                {
                    "operation_id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"mfit-hevy:{import_id}:{workout.order}")),
                    "type": "create_routine",
                    "endpoint": "/v1/routines",
                    "idempotency_key": f"mfit-hevy-{import_id}-{workout.order}",
                    "workout_order": workout.order,
                    "payload": payload,
                    "risk": "high" if errors else "medium",
                    "validation_errors": errors,
                    "warnings": errors,
                }
            )
        return {"import_id": import_id, "operations": operations, "blocked": blocked, "warnings": warnings}

    @staticmethod
    def _exercise_payload(source: SourceExercise, normalized: NormalizedExercise, template_id: str) -> dict:
        sets = []
        count = normalized.sets_min or 1
        for _ in range(count):
            item: dict = (
                {"duration_seconds": normalized.duration_seconds}
                if normalized.is_timed
                else {"reps": normalized.reps_min or 1}
            )
            if normalized.load_value is not None:
                item.update({"weight_kg": normalized.load_value, "weight_unit": normalized.load_unit or "kg"})
            if normalized.rest_seconds is not None:
                item["rest_seconds"] = normalized.rest_seconds
            sets.append(item)
        notes = "; ".join(
            part for part in [source.notes_raw, f"Técnicas: {source.techniques}" if source.techniques else None] if part
        )
        payload = {"exercise_template_id": template_id, "sets": sets}
        if notes:
            payload["notes"] = notes
        return payload
