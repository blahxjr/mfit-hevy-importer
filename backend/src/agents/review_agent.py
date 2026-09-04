"""Gera a visão revisável de uma importação e controla sua aprovação."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.domain.models import ExerciseMapping, SourceExercise, SourceWorkout
from src.repositories.import_repository import ImportRepository


class ReviewAgent:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.import_repo = ImportRepository(db)

    def generate_review(self, import_id: str) -> dict:
        imported = self.import_repo.get_by_id(import_id)
        if not imported:
            return {"error": "Import not found"}
        workouts = self.db.scalars(
            select(SourceWorkout)
            .options(selectinload(SourceWorkout.exercises))
            .where(SourceWorkout.import_id == import_id)
            .order_by(SourceWorkout.order)
        ).all()
        mappings = {item.source_name: item for item in self.db.scalars(select(ExerciseMapping)).all()}
        review_workouts, total, mapped, pending, missing = [], 0, 0, 0, 0
        for workout in workouts:
            exercises = []
            for exercise in sorted(workout.exercises, key=lambda item: item.order):
                mapping = mappings.get(exercise.source_name)
                needs_review = mapping is None or not mapping.confirmed_by_user or mapping.template_id is None
                if mapping:
                    mapped += 1
                if needs_review:
                    pending += 1
                if mapping is None or mapping.template_id is None:
                    missing += 1
                exercises.append(
                    {
                        "source_name": exercise.source_name,
                        "order": exercise.order,
                        "sets_raw": exercise.sets_raw,
                        "reps_raw": exercise.reps_raw,
                        "load_raw": exercise.load_raw,
                        "rest_raw": exercise.rest_raw,
                        "techniques": exercise.techniques,
                        "mapping": {
                            "mapping_id": mapping.id if mapping else None,
                            "template_id": mapping.template_id if mapping else None,
                            "template_title": mapping.template.title if mapping and mapping.template else None,
                            "method": mapping.method if mapping else None,
                            "confidence": mapping.confidence if mapping else None,
                            "needs_review": needs_review,
                        },
                    }
                )
                total += 1
            review_workouts.append(
                {
                    "workout_name": workout.source_name,
                    "order": workout.order,
                    "status": workout.status,
                    "exercises": exercises,
                }
            )
        return {
            "import_id": imported.id,
            "filename": imported.filename,
            "status": imported.status,
            "workouts": review_workouts,
            "summary": {
                "total_exercises": total,
                "mapped_count": mapped,
                "needs_review_count": pending,
                "no_match_count": missing,
            },
        }

    def approve_plan(self, import_id: str) -> dict:
        review = self.generate_review(import_id)
        if "error" in review:
            return review
        workouts = self.db.scalars(select(SourceWorkout).where(SourceWorkout.import_id == import_id)).all()
        if any(workout.status not in {"approved", "completed"} for workout in workouts):
            return {"error": "All workouts must be approved before global approval", "review": review["summary"]}
        imported = self.import_repo.get_by_id(import_id)
        imported.status = "approved"
        self.db.commit()
        return {"success": True, "import_id": import_id, "status": "approved"}

    def approve_workout(self, import_id: str, workout_order: int) -> dict:
        workout = self.db.scalar(
            select(SourceWorkout)
            .options(selectinload(SourceWorkout.exercises))
            .where(SourceWorkout.import_id == import_id, SourceWorkout.order == workout_order)
        )
        if not workout:
            return {"error": "Workout not found"}
        mappings = {item.source_name: item for item in self.db.scalars(select(ExerciseMapping)).all()}
        pending = [
            exercise.source_name
            for exercise in workout.exercises
            if not (mapping := mappings.get(exercise.source_name))
            or not mapping.template_id
            or not mapping.confirmed_by_user
        ]
        if pending:
            return {"error": "All workout mappings must be confirmed", "pending_exercises": pending}
        workout.status = "approved"
        all_workouts = self.db.scalars(select(SourceWorkout).where(SourceWorkout.import_id == import_id)).all()
        imported = self.import_repo.get_by_id(import_id)
        if all(item.status in {"approved", "completed"} for item in all_workouts):
            imported.status = "approved"
        self.db.commit()
        return {"success": True, "import_id": import_id, "workout_order": workout_order, "status": workout.status}
