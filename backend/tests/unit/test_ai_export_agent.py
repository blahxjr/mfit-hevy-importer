import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.agents.ai_export_agent import AIExportAgent, ExportStorageError, UnsafeImportIdError
from src.domain.models import Base, ExerciseCanonicalization, ExerciseMapping, Import, SourceExercise, SourceWorkout


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    engine.dispose()


def create_import(db_session):
    imported = Import(
        id="export-import-1",
        filename="ficha_mfit.pdf",
        sha256="e" * 64,
    )
    workout_late = SourceWorkout(import_ref=imported, source_name="B - Costas", order=2)
    workout_early = SourceWorkout(import_ref=imported, source_name="A - Peito", order=1)
    SourceExercise(
        workout_ref=workout_late,
        source_name="Puxada alta",
        order=2,
        sets_raw="3 x 10",
        reps_raw="10",
        load_raw="50%",
        rest_raw="60s",
        notes_raw="Sem balanço",
        techniques="dropset;rest-pause",
        group_id=7,
    )
    SourceExercise(
        workout_ref=workout_early,
        source_name="Supino reto",
        order=2,
        sets_raw="4 x 8",
        reps_raw="8",
        load_raw="20 kg",
        rest_raw="90s",
        notes_raw=None,
        techniques='["8x8"]',
        group_id=None,
    )
    SourceExercise(workout_ref=workout_early, source_name="Crucifixo", order=1, techniques=None)
    db_session.add(imported)
    db_session.commit()
    return imported


def test_export_creates_utf8_context_and_prompt_in_order(db_session, tmp_path, monkeypatch):
    imported = create_import(db_session)
    monkeypatch.setenv("AI_EXPORT_ROOT", str(tmp_path))

    result = AIExportAgent(db_session).export_import_for_external_ai(imported.id)

    assert result["status"] == "exported"
    assert result["regenerated"] is False
    assert result["workouts_count"] == 2
    assert result["exercises_count"] == 3
    assert not Path(result["prompt_relative_path"]).is_absolute()
    context_path = tmp_path / imported.id / result["context_filename"]
    prompt_path = tmp_path / imported.id / result["prompt_filename"]
    context_text = context_path.read_text(encoding="utf-8")
    prompt_text = prompt_path.read_text(encoding="utf-8")
    context = json.loads(context_text)

    assert context["source_filename"] == "ficha_mfit.pdf"
    assert [workout["source_workout_name_pt"] for workout in context["workouts"]] == [
        "A - Peito",
        "B - Costas",
    ]
    assert [exercise["source_name_pt"] for exercise in context["workouts"][0]["exercises"]] == [
        "Crucifixo",
        "Supino reto",
    ]
    assert context["workouts"][1]["exercises"][0]["techniques"] == ["dropset", "rest-pause"]
    assert "{{MFIT_AI_CONTEXT_JSON}}" not in prompt_text
    assert "ficha_mfit.pdf" in prompt_text
    assert context_text.endswith("\n")


def test_export_has_no_sensitive_or_hevy_data_and_preserves_persistence(db_session, tmp_path, monkeypatch):
    imported = create_import(db_session)
    monkeypatch.setenv("AI_EXPORT_ROOT", str(tmp_path))
    exercise = db_session.query(SourceExercise).first()
    original_name = exercise.source_name
    db_session.add(ExerciseCanonicalization(source_exercise_id=exercise.id, source_name_pt=original_name))
    db_session.commit()

    result = AIExportAgent(db_session).export_import_for_external_ai(imported.id)
    context_text = (tmp_path / imported.id / result["context_filename"]).read_text(encoding="utf-8").lower()
    prompt_text = (tmp_path / imported.id / result["prompt_filename"]).read_text(encoding="utf-8")
    forbidden_values = [
        "api_key",
        "token",
        "password",
        "template_id",
        "hevy_template_id",
        "routine_id",
        "folder_id",
        "user_id",
        "email",
        "phone",
    ]

    assert all(value not in context_text for value in forbidden_values)
    assert "265ae195-b2e3-48fa-a3af-0931bf2dd227" not in prompt_text
    assert db_session.query(ExerciseCanonicalization).count() == 1
    assert db_session.query(ExerciseMapping).count() == 0
    db_session.refresh(exercise)
    assert exercise.source_name == original_name


def test_export_is_deterministic_and_reports_regeneration(db_session, tmp_path, monkeypatch):
    imported = create_import(db_session)
    monkeypatch.setenv("AI_EXPORT_ROOT", str(tmp_path))
    agent = AIExportAgent(db_session)

    first = agent.export_import_for_external_ai(imported.id)
    first_prompt = (tmp_path / imported.id / first["prompt_filename"]).read_bytes()
    first_context = (tmp_path / imported.id / first["context_filename"]).read_bytes()
    second = agent.export_import_for_external_ai(imported.id)

    assert second["regenerated"] is True
    assert second["prompt_filename"] == first["prompt_filename"]
    assert second["context_filename"] == first["context_filename"]
    assert (tmp_path / imported.id / second["prompt_filename"]).read_bytes() == first_prompt
    assert (tmp_path / imported.id / second["context_filename"]).read_bytes() == first_context
    assert sorted(path.name for path in (tmp_path / imported.id).iterdir()) == sorted(
        [first["prompt_filename"], first["context_filename"]]
    )


def test_invalid_import_id_is_rejected(db_session, tmp_path, monkeypatch):
    monkeypatch.setenv("AI_EXPORT_ROOT", str(tmp_path))
    with pytest.raises(UnsafeImportIdError):
        AIExportAgent(db_session).export_import_for_external_ai("../escape")


def test_storage_error_is_controlled(db_session, tmp_path, monkeypatch):
    imported = create_import(db_session)
    monkeypatch.setenv("AI_EXPORT_ROOT", str(tmp_path))
    monkeypatch.setattr(Path, "write_bytes", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("denied")))

    with pytest.raises(ExportStorageError):
        AIExportAgent(db_session).export_import_for_external_ai(imported.id)
