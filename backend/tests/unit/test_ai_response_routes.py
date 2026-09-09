import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.main import app
from src.domain.models import Base, Import, SourceExercise, SourceWorkout
from src.infrastructure.database import get_db


def route_payload():
    return {
        "schema_version": "1.0",
        "import_id": "route-response",
        "source_filename": "route.pdf",
        "generated_by": {"provider": "copilot"},
        "workouts": [
            {
                "source_workout_order": 0,
                "source_workout_name_pt": "A - Rota",
                "exercises": [
                    {
                        "source_exercise_id": 1,
                        "source_exercise_order": 0,
                        "source_name_pt": "Agachamento",
                        "canonical_name_en": "Squat",
                        "search_aliases_en": [],
                        "movement_pattern": "squat",
                        "equipment_hint": "barbell",
                        "primary_muscle_hint": "legs",
                        "secondary_muscles_hint": [],
                        "confidence": 0.7,
                        "needs_review": False,
                        "review_reason": None,
                        "notes_for_hevy_search": None,
                    }
                ],
            }
        ],
    }


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    imported = Import(id="route-response", filename="route.pdf", sha256="q" * 64)
    workout = SourceWorkout(import_ref=imported, source_name="A - Rota", order=0)
    SourceExercise(workout_ref=workout, source_name="Agachamento", order=0)
    session.add(imported)
    session.commit()

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    session.close()
    engine.dispose()


def upload(client, payload, filename="response.json", content_type="application/json"):
    return client.post(
        "/ai-response/import",
        files={"file": (filename, json.dumps(payload).encode("utf-8"), content_type)},
    )


def test_valid_upload_and_validation_report(api_client):
    response = upload(api_client, route_payload())
    assert response.status_code == 200
    assert response.json()["status"] == "imported"
    report = api_client.get("/ai-response/route-response/validation-report")
    assert report.status_code == 200
    assert report.json()["validation_report"]["valid"] is True


def test_file_validation_and_schema_errors(api_client):
    assert upload(api_client, route_payload(), "response.txt").status_code == 400
    assert upload(api_client, route_payload(), "response.json", "text/plain").status_code == 400
    assert upload(api_client, route_payload(), "response.json", "application/json").status_code == 200
    invalid = route_payload()
    invalid["template_id"] = "bad"
    assert upload(api_client, invalid).status_code == 422
    assert upload(api_client, {**route_payload(), "import_id": "missing"}).status_code == 404


def test_oversized_and_missing_report_are_safe(api_client):
    oversized = b"{" + b"x" * (5 * 1024 * 1024) + b"}"
    response = api_client.post(
        "/ai-response/import",
        files={"file": ("large.json", oversized, "application/json")},
    )
    assert response.status_code == 400
    missing = api_client.get("/ai-response/route-response/validation-report")
    assert missing.status_code == 404
    assert "C:\\" not in response.text


def test_inconsistent_response_returns_409_and_report_remains_available(api_client):
    payload = route_payload()
    payload["workouts"][0]["exercises"][0]["source_name_pt"] = "Alterado"
    response = upload(api_client, payload)
    assert response.status_code == 409
    report = api_client.get("/ai-response/route-response/validation-report")
    assert report.status_code == 200
    assert report.json()["validation_report"]["valid"] is False
