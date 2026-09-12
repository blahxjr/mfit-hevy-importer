"""API local de planejamento e execução de treinos."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.agents.workout_engine_agent import WorkoutEngineAgent
from src.infrastructure.database import get_db
from src.repositories.workout_repository import WorkoutRepository

router = APIRouter(tags=["Local workouts"])


def _error(exc: ValueError) -> HTTPException:
    message = str(exc)
    status = 404 if message.endswith("not found") else 409 if "transition" in message or "status" in message or "progress" in message or "planned" in message else 400
    return HTTPException(status, message)


def _set_dto(item) -> dict[str, object]:
    return {"id": item.id, "set_index": item.set_index, "actual_reps": item.actual_reps, "actual_load": item.actual_load,
            "actual_time_seconds": item.actual_time_seconds, "actual_distance_meters": item.actual_distance_meters,
            "rpe": item.rpe, "completed_at": item.completed_at}


def _exercise_dto(item) -> dict[str, object]:
    return {"id": item.id, "exercise_id": item.exercise_id, "exercise_name": item.exercise.name if item.exercise else None,
            "sequence_index": item.sequence_index, "planned_sets": item.planned_sets, "planned_reps": item.planned_reps,
            "planned_load": item.planned_load, "planned_time_seconds": item.planned_time_seconds,
            "planned_distance_meters": item.planned_distance_meters, "notes": item.notes,
            "set_logs": [_set_dto(log) for log in item.set_logs]}


def _workout_dto(item, include_exercises: bool = True) -> dict[str, object]:
    result = {"id": item.id, "import_id": item.import_id, "hevy_workout_id": item.hevy_workout_id,
              "hevy_routine_id": item.hevy_routine_id, "name": item.name, "date": item.date,
              "status": item.status, "notes": item.notes, "created_at": item.created_at, "updated_at": item.updated_at}
    if include_exercises:
        result["exercises"] = [_exercise_dto(exercise) for exercise in item.exercises]
    return result


@router.post("/workouts/from-import/{import_id}")
def create_from_import(import_id: str, db: Session = Depends(get_db)):
    try:
        return _workout_dto(WorkoutEngineAgent(db).create_workout_from_import(import_id))
    except ValueError as exc:
        raise _error(exc) from exc


@router.post("/workouts/from-hevy-routine/{routine_id}")
def create_from_hevy_routine(routine_id: str, db: Session = Depends(get_db)):
    try:
        return _workout_dto(WorkoutEngineAgent(db).create_workout_from_hevy_routine(routine_id))
    except ValueError as exc:
        raise _error(exc) from exc


@router.get("/workouts")
def list_workouts(date_from: datetime | None = None, date_to: datetime | None = None, status: str | None = Query(None), db: Session = Depends(get_db)):
    return {"workouts": [_workout_dto(item, False) for item in WorkoutRepository(db).list_by_date_range(date_from, date_to, status)]}


@router.get("/workouts/{workout_id}")
def get_workout(workout_id: str, db: Session = Depends(get_db)):
    item = WorkoutRepository(db).get_by_id(workout_id)
    if item is None:
        raise HTTPException(404, "Workout not found")
    return _workout_dto(item)


def _transition(workout_id: str, action: str, db: Session):
    try:
        method = {"start": "start_workout", "complete": "complete_workout", "abort": "abort_workout"}[action]
        return _workout_dto(getattr(WorkoutEngineAgent(db), method)(workout_id))
    except ValueError as exc:
        raise _error(exc) from exc


@router.post("/workouts/{workout_id}/start")
def start_workout(workout_id: str, db: Session = Depends(get_db)):
    return _transition(workout_id, "start", db)


@router.post("/workouts/{workout_id}/complete")
def complete_workout(workout_id: str, db: Session = Depends(get_db)):
    return _transition(workout_id, "complete", db)


@router.post("/workouts/{workout_id}/abort")
def abort_workout(workout_id: str, db: Session = Depends(get_db)):
    return _transition(workout_id, "abort", db)


@router.post("/workouts/{workout_id}/exercises")
def add_exercise(workout_id: str, payload: dict[str, object], db: Session = Depends(get_db)):
    try:
        exercise_id = payload.get("exercise_id")
        if not isinstance(exercise_id, str):
            raise ValueError("exercise_id is required")
        planned = {key: payload[key] for key in ("planned_sets", "planned_reps", "planned_load", "planned_time_seconds", "planned_distance_meters", "notes") if key in payload}
        return _exercise_dto(WorkoutEngineAgent(db).add_exercise_to_workout(workout_id, exercise_id, **planned))
    except ValueError as exc:
        raise _error(exc) from exc


@router.post("/workout-exercises/{workout_exercise_id}/sets/log")
def log_set(workout_exercise_id: str, payload: dict[str, object], db: Session = Depends(get_db)):
    try:
        set_index = payload.get("set_index")
        if not isinstance(set_index, int):
            raise ValueError("set_index is required")
        actual = {key: payload[key] for key in ("actual_reps", "actual_load", "actual_time_seconds", "actual_distance_meters", "rpe") if key in payload}
        item = WorkoutEngineAgent(db).log_set(workout_exercise_id, set_index, **actual)
        return _set_dto(item)
    except ValueError as exc:
        raise _error(exc) from exc