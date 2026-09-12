from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.domain.models import WorkoutExercise


class WorkoutExerciseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add_exercise_to_workout(self, workout_id: str, exercise_id: str, *, sequence_index: int,
                                planned_sets: int = 1, planned_reps: int | None = None,
                                planned_load: str | float | None = None, planned_time_seconds: int | None = None,
                                planned_distance_meters: int | None = None, notes: str | None = None) -> WorkoutExercise:
        item = WorkoutExercise(id=str(uuid4()), workout_id=workout_id, exercise_id=exercise_id,
                               sequence_index=sequence_index, planned_sets=planned_sets,
                               planned_reps=planned_reps, planned_load=None if planned_load is None else str(planned_load),
                               planned_time_seconds=planned_time_seconds, planned_distance_meters=planned_distance_meters,
                               notes=notes)
        self.db.add(item)
        return item

    def get_by_id(self, workout_exercise_id: str) -> WorkoutExercise | None:
        return self.db.scalar(select(WorkoutExercise).options(selectinload(WorkoutExercise.workout)).where(WorkoutExercise.id == workout_exercise_id))

    def list_by_workout(self, workout_id: str) -> list[WorkoutExercise]:
        return list(self.db.scalars(select(WorkoutExercise).options(selectinload(WorkoutExercise.set_logs), selectinload(WorkoutExercise.exercise)).where(WorkoutExercise.workout_id == workout_id).order_by(WorkoutExercise.sequence_index)))