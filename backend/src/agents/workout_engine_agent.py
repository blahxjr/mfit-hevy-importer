"""Fachada da execução local; não possui cliente Hevy ou Strava."""

from sqlalchemy.orm import Session

from src.services.workout_engine_service import WorkoutEngineService


class WorkoutEngineAgent:
    def __init__(self, db: Session) -> None:
        self.service = WorkoutEngineService(db)

    def create_workout_from_import(self, import_id: str):
        return self.service.create_from_import(import_id)

    def create_workout_from_hevy_routine(self, routine_id: str):
        return self.service.create_from_hevy_routine(routine_id)

    def add_exercise_to_workout(self, workout_id: str, exercise_id: str, **planned: object):
        return self.service.add_exercise(workout_id, exercise_id, **planned)

    def start_workout(self, workout_id: str):
        return self.service.transition(workout_id, "in_progress")

    def complete_workout(self, workout_id: str):
        return self.service.transition(workout_id, "completed")

    def abort_workout(self, workout_id: str):
        return self.service.transition(workout_id, "aborted")

    def log_set(self, workout_exercise_id: str, set_index: int, **actual: object):
        return self.service.log_set(workout_exercise_id, set_index, **actual)