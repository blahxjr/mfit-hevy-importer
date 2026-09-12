from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.domain.models import Base, Exercise, ExerciseTemplate, Import, Routine, SourceExercise, SourceWorkout
from src.services.workout_engine_service import WorkoutEngineService


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_create_execute_and_upsert_set():
    db = setup_db()
    imported = Import(id="import-1", filename="treino.pdf", sha256="a" * 64)
    source_workout = SourceWorkout(import_id=imported.id, source_name="A", order=0)
    source_exercise = SourceExercise(workout_ref=source_workout, source_name="Agachamento", order=0, sets_raw="3", reps_raw="10", load_raw="20 kg")
    db.add_all([imported, source_workout, source_exercise])
    db.commit()
    service = WorkoutEngineService(db)
    workout = service.create_from_import(imported.id)
    assert workout.status == "planned"
    assert workout.exercises[0].planned_sets == 3
    service.transition(workout.id, "in_progress")
    log = service.log_set(workout.exercises[0].id, 0, actual_reps=10, actual_load=20.0, rpe=8)
    assert log.rpe == 8
    same = service.log_set(workout.exercises[0].id, 0, actual_reps=9, actual_load=21.0, rpe=9)
    assert same.id == log.id
    assert same.actual_reps == 9
    service.transition(workout.id, "completed")
    assert db.get(type(workout), workout.id).status == "completed"


def test_transitions_and_manual_exercise():
    db = setup_db()
    exercise = Exercise(id="exercise-1", name="Bench Press", source="custom")
    db.add(exercise)
    db.commit()
    service = WorkoutEngineService(db)
    workout = service.workouts.create_planned_workout(None, "Manual", datetime.now(timezone.utc))
    db.commit()
    service.add_exercise(workout.id, exercise.id, planned_sets=2, planned_reps=8)
    service.transition(workout.id, "in_progress")
    try:
        service.transition(workout.id, "planned")
        assert False, "transition should be rejected"
    except ValueError as exc:
        assert "transition" in str(exc)
    try:
        service.log_set(workout.exercises[0].id, 0, actual_reps=8, rpe=11)
        assert False, "invalid RPE should be rejected"
    except ValueError as exc:
        assert "rpe" in str(exc)


def test_create_from_hevy_routine_is_local_only():
    db = setup_db()
    db.add_all([Routine(id="routine-1", title="Upper body", exercise_plan='[{"template_id": "template-1", "sets": [{"reps": 8, "weight": 20}], "notes": "Controlado"}]'), ExerciseTemplate(id="template-1", title="Bench Press")])
    db.flush()
    db.add(Exercise(id="exercise-1", name="Bench Press", source="exercisedb", hevy_template_id="template-1"))
    db.commit()
    workout = WorkoutEngineService(db).create_from_hevy_routine("routine-1")
    assert workout.hevy_routine_id == "routine-1"
    assert workout.import_id is None
    assert workout.status == "planned"
    assert len(workout.exercises) == 1
    assert workout.exercises[0].planned_reps == 8
