from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.models import WorkoutSetLog


class WorkoutSetLogRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def log_set(self, workout_exercise_id: str, set_index: int, *, actual_reps: int | None = None,
                actual_load: str | float | None = None, actual_time_seconds: int | None = None,
                actual_distance_meters: int | None = None, rpe: int | None = None,
                completed_at: datetime | None = None) -> WorkoutSetLog:
        item = self.db.scalar(select(WorkoutSetLog).where(WorkoutSetLog.workout_exercise_id == workout_exercise_id,
                                                            WorkoutSetLog.set_index == set_index))
        if item is None:
            item = WorkoutSetLog(id=str(uuid4()), workout_exercise_id=workout_exercise_id, set_index=set_index)
            self.db.add(item)
        item.actual_reps = actual_reps
        item.actual_load = None if actual_load is None else str(actual_load)
        item.actual_time_seconds = actual_time_seconds
        item.actual_distance_meters = actual_distance_meters
        item.rpe = rpe
        item.completed_at = completed_at or datetime.now(timezone.utc)
        return item

    def list_by_workout_exercise(self, workout_exercise_id: str) -> list[WorkoutSetLog]:
        return list(self.db.scalars(select(WorkoutSetLog).where(WorkoutSetLog.workout_exercise_id == workout_exercise_id).order_by(WorkoutSetLog.set_index)))