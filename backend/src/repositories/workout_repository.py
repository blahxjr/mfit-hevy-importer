from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.domain.models import Workout, WorkoutExercise


class WorkoutRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_planned_workout(self, import_id: str | None, name: str, date: datetime, notes: str | None = None,
                               hevy_routine_id: str | None = None) -> Workout:
        workout = Workout(id=str(uuid4()), import_id=import_id, name=name, date=date, notes=notes,
                          hevy_routine_id=hevy_routine_id, status="planned")
        self.db.add(workout)
        return workout

    def get_by_id(self, workout_id: str) -> Workout | None:
        return self.db.scalar(
            select(Workout).options(selectinload(Workout.exercises).selectinload(WorkoutExercise.set_logs),
                                    selectinload(Workout.exercises).selectinload(WorkoutExercise.exercise)).where(Workout.id == workout_id)
        )

    def list_by_date_range(self, date_from: datetime | None = None, date_to: datetime | None = None,
                           status: str | None = None) -> list[Workout]:
        query = select(Workout).order_by(Workout.date.desc())
        if date_from is not None:
            query = query.where(Workout.date >= date_from)
        if date_to is not None:
            query = query.where(Workout.date <= date_to)
        if status:
            query = query.where(Workout.status == status)
        return list(self.db.scalars(query))

    def update_status(self, workout_id: str, status: str) -> Workout:
        workout = self.db.get(Workout, workout_id)
        if workout is None:
            raise ValueError("Workout not found")
        workout.status = status
        return workout