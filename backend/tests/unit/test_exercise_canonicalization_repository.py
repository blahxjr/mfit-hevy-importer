import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from src.domain.models import Base, ExerciseCanonicalization, ExerciseMapping, Import, SourceExercise, SourceWorkout
from src.repositories.exercise_canonicalization_repository import (
    ExerciseCanonicalizationRepository,
    deserialize_string_list,
)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    engine.dispose()


def create_import_graph(db_session):
    imported = Import(id="import-canonicalization", filename="ficha.pdf", sha256="c" * 64)
    workout = SourceWorkout(import_ref=imported, source_name="Treino A", order=0)
    exercise = SourceExercise(workout_ref=workout, source_name="Supino reto", order=0)
    db_session.add(imported)
    db_session.commit()
    return imported, workout, exercise


def canonicalization_values(source_exercise_id, **overrides):
    values = {
        "source_exercise_id": source_exercise_id,
        "source_name_pt": "Supino reto",
        "canonical_name_en": "Barbell Bench Press",
        "search_aliases_en": ["Flat Bench Press", "Bench Press"],
        "movement_pattern": "horizontal_push",
        "equipment_hint": "barbell",
        "primary_muscle_hint": "pectoralis major",
        "secondary_muscles_hint": ["triceps", "anterior deltoid"],
        "confidence": 0.8,
        "needs_review": True,
        "review_reason": "Revisão humana obrigatória.",
        "provider": "external_ai",
        "model_name": "manual-test",
        "prompt_version": "v1",
        "raw_response_sanitized": '{"provider":"external_ai"}',
    }
    values.update(overrides)
    return values


def test_create_persists_all_main_fields_and_defaults(db_session):
    _, _, exercise = create_import_graph(db_session)
    repository = ExerciseCanonicalizationRepository(db_session)

    saved = repository.upsert(**canonicalization_values(exercise.id))

    assert saved.source_exercise_id == exercise.id
    assert saved.source_name_pt == "Supino reto"
    assert saved.canonical_name_en == "Barbell Bench Press"
    assert json.loads(saved.search_aliases_en) == ["Flat Bench Press", "Bench Press"]
    assert saved.movement_pattern == "horizontal_push"
    assert saved.equipment_hint == "barbell"
    assert saved.primary_muscle_hint == "pectoralis major"
    assert json.loads(saved.secondary_muscles_hint) == ["triceps", "anterior deltoid"]
    assert saved.confidence == 0.8
    assert saved.needs_review is True
    assert saved.provider == "external_ai"
    assert saved.prompt_version == "v1"


def test_get_by_source_exercise_id_returns_entity_or_none(db_session):
    _, _, exercise = create_import_graph(db_session)
    repository = ExerciseCanonicalizationRepository(db_session)
    saved = repository.upsert(**canonicalization_values(exercise.id))

    assert repository.get_by_source_exercise_id(exercise.id) is saved
    assert repository.get_by_source_exercise_id(99999) is None
    assert repository.get_by_id(saved.id) is saved


def test_upsert_updates_without_creating_duplicate(db_session):
    _, _, exercise = create_import_graph(db_session)
    repository = ExerciseCanonicalizationRepository(db_session)
    repository.upsert(**canonicalization_values(exercise.id))

    updated = repository.upsert(
        **canonicalization_values(
            exercise.id,
            search_aliases_en=["Dumbbell Bench Press"],
            confidence=0.35,
            needs_review=False,
            canonical_name_en="Updated Bench Press",
        )
    )

    assert db_session.query(ExerciseCanonicalization).count() == 1
    assert updated.canonical_name_en == "Updated Bench Press"
    assert json.loads(updated.search_aliases_en) == ["Dumbbell Bench Press"]
    assert updated.confidence == 0.35
    assert updated.needs_review is False


def test_unique_constraint_rejects_second_direct_insert(db_session):
    _, _, exercise = create_import_graph(db_session)
    repository = ExerciseCanonicalizationRepository(db_session)
    repository.upsert(**canonicalization_values(exercise.id))

    duplicate_values = canonicalization_values(exercise.id)
    duplicate_values["search_aliases_en"] = json.dumps(duplicate_values["search_aliases_en"])
    duplicate_values["secondary_muscles_hint"] = json.dumps(duplicate_values["secondary_muscles_hint"])
    db_session.add(ExerciseCanonicalization(**duplicate_values))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
    assert db_session.query(ExerciseCanonicalization).count() == 1


def test_get_by_import_id_orders_by_workout_and_exercise(db_session):
    imported = Import(id="ordered-import", filename="ordered.pdf", sha256="o" * 64)
    workout_late = SourceWorkout(import_ref=imported, source_name="B", order=2)
    workout_early = SourceWorkout(import_ref=imported, source_name="A", order=1)
    exercise_late = SourceExercise(workout_ref=workout_late, source_name="late", order=0)
    exercise_early_late = SourceExercise(workout_ref=workout_early, source_name="early-late", order=2)
    exercise_early_first = SourceExercise(workout_ref=workout_early, source_name="early-first", order=1)
    db_session.add(imported)
    db_session.commit()
    repository = ExerciseCanonicalizationRepository(db_session)

    for exercise in (exercise_late, exercise_early_late, exercise_early_first):
        repository.upsert(**canonicalization_values(exercise.id, source_name_pt=exercise.source_name))

    result = repository.get_by_import_id(imported.id)
    assert [item.source_name_pt for item in result] == ["early-first", "early-late", "late"]


def test_serialization_helpers_are_safe_and_return_lists(db_session):
    _, _, exercise = create_import_graph(db_session)
    repository = ExerciseCanonicalizationRepository(db_session)
    saved = repository.upsert(
        **canonicalization_values(
            exercise.id,
            search_aliases_en=["Alias"],
            secondary_muscles_hint=["Triceps"],
        )
    )

    assert json.loads(saved.search_aliases_en) == ["Alias"]
    assert json.loads(saved.secondary_muscles_hint) == ["Triceps"]
    assert deserialize_string_list(None) == []
    assert deserialize_string_list("not-json") == []
    assert deserialize_string_list('{"not": "a list"}') == []
    assert deserialize_string_list("[1, 2]") == []


def test_upsert_preserves_source_and_does_not_create_mapping(db_session):
    _, _, exercise = create_import_graph(db_session)
    original_name = exercise.source_name
    repository = ExerciseCanonicalizationRepository(db_session)

    repository.upsert(**canonicalization_values(exercise.id, source_name_pt="Nome auditado"))
    db_session.refresh(exercise)

    assert exercise.source_name == original_name
    assert db_session.query(ExerciseMapping).count() == 0


def test_cascade_deletes_canonicalization_with_source_exercise(db_session):
    _, workout, exercise = create_import_graph(db_session)
    repository = ExerciseCanonicalizationRepository(db_session)
    repository.upsert(**canonicalization_values(exercise.id))

    db_session.delete(exercise)
    db_session.commit()

    assert db_session.query(ExerciseCanonicalization).count() == 0
