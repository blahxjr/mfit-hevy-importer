import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.agents.ai_response_import_agent import (
    AIResponseImportAgent,
    ResponseImportMismatchError,
    ResponseImportNotFoundError,
    ResponsePayloadError,
)
from src.domain.models import Base, ExerciseCanonicalization, ExerciseMapping, Import, SourceExercise, SourceWorkout


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    engine.dispose()


def create_local_import(db_session):
    imported = Import(id="response-import", filename="response.pdf", sha256="z" * 64)
    workout_a = SourceWorkout(import_ref=imported, source_name="A - Peito", order=0)
    workout_b = SourceWorkout(import_ref=imported, source_name="B - Costas", order=1)
    SourceExercise(workout_ref=workout_a, source_name="Supino", order=0)
    SourceExercise(workout_ref=workout_b, source_name="Remada", order=0)
    db_session.add(imported)
    db_session.commit()
    return imported


def response_payload(import_id="response-import", filename="response.pdf"):
    def exercise(exercise_id, name, canonical):
        return {
            "source_exercise_id": exercise_id,
            "source_exercise_order": 0,
            "source_name_pt": name,
            "canonical_name_en": canonical,
            "search_aliases_en": [canonical],
            "movement_pattern": "horizontal_push",
            "equipment_hint": "barbell",
            "primary_muscle_hint": "chest",
            "secondary_muscles_hint": ["triceps"],
            "confidence": 0.9,
            "needs_review": False,
            "review_reason": None,
            "notes_for_hevy_search": "local note",
        }

    return {
        "schema_version": "1.0",
        "import_id": import_id,
        "source_filename": filename,
        "generated_by": {"provider": "chatgpt", "model": "test"},
        "workouts": [
            {
                "source_workout_order": 0,
                "source_workout_name_pt": "A - Peito",
                "exercises": [exercise(1, "Supino", "Bench Press")],
            },
            {
                "source_workout_order": 1,
                "source_workout_name_pt": "B - Costas",
                "exercises": [exercise(2, "Remada", "Row")],
            },
        ],
    }


def payload_bytes(payload):
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def test_valid_import_persists_only_canonicalizations_and_forces_review(db_session):
    create_local_import(db_session)
    result = AIResponseImportAgent(db_session).import_external_ai_response(payload_bytes(response_payload()))

    assert result["status"] == "imported"
    assert result["accepted_count"] == 2
    assert result["created_count"] == 2
    assert result["updated_count"] == 0
    rows = db_session.query(ExerciseCanonicalization).all()
    assert len(rows) == 2
    assert all(row.needs_review is True for row in rows)
    assert db_session.query(ExerciseMapping).count() == 0
    assert all("local note" not in (row.raw_response_sanitized or "") for row in rows)


def test_invalid_json_encoding_empty_and_oversized_are_rejected(db_session):
    agent = AIResponseImportAgent(db_session)
    for content in (b"", b"{invalid", b"\xff\xfe"):
        with pytest.raises(ResponsePayloadError):
            agent.import_external_ai_response(content)
    with pytest.raises(ResponsePayloadError):
        agent.import_external_ai_response(b"x" * (5 * 1024 * 1024 + 1))


def test_missing_import_and_filename_mismatch_are_rejected(db_session):
    agent = AIResponseImportAgent(db_session)
    with pytest.raises(ResponseImportNotFoundError):
        agent.import_external_ai_response(payload_bytes(response_payload("missing")))
    create_local_import(db_session)
    with pytest.raises(ResponseImportMismatchError):
        agent.import_external_ai_response(payload_bytes(response_payload(filename="other.pdf")))
    assert db_session.query(ExerciseCanonicalization).count() == 0


@pytest.mark.parametrize(
    "mutation", ["extra_workout", "missing_workout", "extra_exercise", "wrong_order", "wrong_name"]
)
def test_structural_inconsistencies_reject_without_persisting(db_session, mutation):
    create_local_import(db_session)
    payload = response_payload()
    if mutation == "extra_workout":
        payload["workouts"].append(
            {"source_workout_order": 2, "source_workout_name_pt": "C", "exercises": payload["workouts"][0]["exercises"]}
        )
    elif mutation == "missing_workout":
        payload["workouts"].pop()
    elif mutation == "extra_exercise":
        payload["workouts"][0]["exercises"].append(
            dict(payload["workouts"][1]["exercises"][0], source_exercise_id=99, source_name_pt="Extra")
        )
    elif mutation == "wrong_order":
        payload["workouts"][0]["exercises"][0]["source_exercise_order"] = 8
    elif mutation == "wrong_name":
        payload["workouts"][0]["exercises"][0]["source_name_pt"] = "Alterado"

    result = AIResponseImportAgent(db_session).import_external_ai_response(payload_bytes(payload))
    assert result["status"] == "rejected"
    assert result["validation_report"]["valid"] is False
    assert db_session.query(ExerciseCanonicalization).count() == 0


def test_idempotency_updates_same_rows_and_preserves_source(db_session):
    create_local_import(db_session)
    agent = AIResponseImportAgent(db_session)
    first = agent.import_external_ai_response(payload_bytes(response_payload()))
    payload = response_payload()
    payload["workouts"][0]["exercises"][0]["canonical_name_en"] = "Updated Bench Press"
    second = agent.import_external_ai_response(payload_bytes(payload))

    assert first["created_count"] == 2
    assert second["created_count"] == 0
    assert second["updated_count"] == 2
    assert db_session.query(ExerciseCanonicalization).count() == 2
    assert db_session.query(SourceExercise).filter_by(source_name="Supino").count() == 1
