"""Regras de domínio para planejar e executar treinos localmente."""

import json
import re
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.models import Exercise, ExerciseTemplate, Import, Routine, SourceWorkout, Workout
from src.repositories.exercise_repository import ExerciseRepository, normalize_name
from src.repositories.workout_exercise_repository import WorkoutExerciseRepository
from src.repositories.workout_repository import WorkoutRepository
from src.repositories.workout_set_log_repository import WorkoutSetLogRepository


class WorkoutEngineService:
    VALID_STATUSES = {"planned", "in_progress", "completed", "aborted"}
    TRANSITIONS = {"planned": {"in_progress", "aborted"}, "in_progress": {"completed", "aborted"}, "completed": set(), "aborted": set()}

    def __init__(self, db: Session) -> None:
        self.db = db
        self.workouts = WorkoutRepository(db)
        self.exercises = WorkoutExerciseRepository(db)
        self.logs = WorkoutSetLogRepository(db)
        self.catalog = ExerciseRepository(db)

    @staticmethod
    def _first_int(value: str | None) -> int | None:
        if not value:
            return None
        match = re.search(r"\d+", value)
        return int(match.group()) if match else None

    def _resolve_catalog_exercise(self, name: str) -> Exercise:
        found = self.catalog.search(name=name, limit=1)
        if found:
            return found[0]
        found = self.catalog.search(name=normalize_name(name), limit=1)
        if found:
            return found[0]
        item = Exercise(id=__import__("uuid").uuid4().__str__(), name=name, name_en=name, source="custom")
        self.db.add(item)
        self.db.flush()
        return item

    def create_from_import(self, import_id: str) -> Workout:
        imported = self.db.get(Import, import_id)
        if imported is None:
            raise ValueError("Import not found")
        workout = self.workouts.create_planned_workout(import_id, imported.filename.rsplit(".", 1)[0], datetime.now(timezone.utc))
        source_workouts = list(self.db.scalars(select(SourceWorkout).where(SourceWorkout.import_id == import_id).order_by(SourceWorkout.order)))
        sequence = 0
        for source_workout in source_workouts:
            for source_exercise in sorted(source_workout.exercises, key=lambda item: item.order):
                normalized = source_exercise.normalized
                exercise = self._resolve_catalog_exercise(source_exercise.source_name)
                self.exercises.add_exercise_to_workout(workout.id, exercise.id, sequence_index=sequence,
                    planned_sets=self._first_int(normalized.sets_raw if normalized else source_exercise.sets_raw) or 1,
                    planned_reps=self._first_int(normalized.reps_raw if normalized else source_exercise.reps_raw),
                    planned_load=(normalized.load_value if normalized and normalized.load_value is not None else source_exercise.load_raw),
                    planned_time_seconds=normalized.duration_seconds if normalized else None,
                    notes=source_exercise.notes_raw)
                sequence += 1
        self.db.commit()
        return self.workouts.get_by_id(workout.id)  # type: ignore[return-value]

    def create_from_hevy_routine(self, routine_id: str) -> Workout:
        routine = self.db.get(Routine, routine_id)
        if routine is None:
            raise ValueError("Routine not found")
        workout = self.workouts.create_planned_workout(None, routine.title, datetime.now(timezone.utc), hevy_routine_id=routine.id)
        plan = json.loads(routine.exercise_plan or "[]")
        for index, planned in enumerate(plan):
            if not isinstance(planned, dict):
                continue
            template_id = planned.get("template_id")
            exercise = self.db.scalar(select(Exercise).where(Exercise.hevy_template_id == str(template_id))) if template_id else None
            if exercise is None and template_id:
                template = self.db.get(ExerciseTemplate, str(template_id))
                if template is not None:
                    exercise = self._resolve_catalog_exercise(template.title)
                    exercise.hevy_template_id = template.id
            if exercise is None:
                continue
            sets = planned.get("sets") if isinstance(planned.get("sets"), list) else []
            first_set = sets[0] if sets and isinstance(sets[0], dict) else {}
            self.exercises.add_exercise_to_workout(
                workout.id, exercise.id, sequence_index=index,
                planned_sets=max(len(sets), 1), planned_reps=first_set.get("reps"),
                planned_load=first_set.get("weight"), notes=planned.get("notes"),
            )
        self.db.commit()
        return self.workouts.get_by_id(workout.id)  # type: ignore[return-value]

    def add_exercise(self, workout_id: str, exercise_id: str, **planned: object):
        workout = self.db.get(Workout, workout_id)
        if workout is None:
            raise ValueError("Workout not found")
        if workout.status != "planned":
            raise ValueError("Only planned workouts can be edited")
        if self.catalog.get_by_id(exercise_id) is None:
            raise ValueError("Exercise not found")
        current = self.exercises.list_by_workout(workout_id)
        item = self.exercises.add_exercise_to_workout(workout_id, exercise_id, sequence_index=len(current), **planned)
        self.db.commit()
        return item

    def transition(self, workout_id: str, status: str) -> Workout:
        if status not in self.VALID_STATUSES:
            raise ValueError("Invalid workout status")
        workout = self.db.get(Workout, workout_id)
        if workout is None:
            raise ValueError("Workout not found")
        if status not in self.TRANSITIONS[workout.status]:
            raise ValueError(f"Invalid transition: {workout.status} -> {status}")
        workout.status = status
        self.db.commit()
        return self.workouts.get_by_id(workout_id)  # type: ignore[return-value]

    def log_set(self, workout_exercise_id: str, set_index: int, **actual: object):
        if set_index < 0:
            raise ValueError("set_index must be non-negative")
        item = self.exercises.get_by_id(workout_exercise_id)
        if item is None:
            raise ValueError("Workout exercise not found")
        if item.workout.status != "in_progress":
            raise ValueError("Workout must be in progress")
        rpe = actual.get("rpe")
        if rpe is not None and (not isinstance(rpe, int) or not 1 <= rpe <= 10):
            raise ValueError("rpe must be between 1 and 10")
        result = self.logs.log_set(workout_exercise_id, set_index, **actual)
        self.db.commit()
        return result