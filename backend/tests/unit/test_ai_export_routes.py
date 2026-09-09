import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.main import app
from src.domain.models import Base, Import, SourceExercise, SourceWorkout
from src.infrastructure.database import get_db


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    imported = Import(id="route-import", filename="rota.pdf", sha256="r" * 64)
    workout = SourceWorkout(import_ref=imported, source_name="A - Rota", order=0)
    SourceExercise(workout_ref=workout, source_name="Agachamento", order=0)
    session.add(imported)
    session.commit()
    monkeypatch.setenv("AI_EXPORT_ROOT", str(tmp_path))

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    session.close()
    engine.dispose()


def test_generate_and_download_external_ai_package(api_client):
    response = api_client.post("/ai-export/route-import")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "exported"
    assert body["workouts_count"] == 1
    assert body["exercises_count"] == 1
    assert not body["prompt_relative_path"].startswith("/")
    assert not body["context_relative_path"].startswith("/")

    prompt = api_client.get("/ai-export/route-import/download/prompt")
    context = api_client.get("/ai-export/route-import/download/context")
    assert prompt.status_code == 200
    assert prompt.headers["content-type"].startswith("text/markdown")
    assert "attachment" in prompt.headers["content-disposition"]
    assert context.status_code == 200
    assert context.headers["content-type"].startswith("application/json")
    assert "attachment" in context.headers["content-disposition"]


def test_missing_import_and_download_before_generation_return_404(api_client):
    assert api_client.post("/ai-export/missing").status_code == 404
    assert api_client.get("/ai-export/missing/download/prompt").status_code == 404
    assert api_client.get("/ai-export/missing/download/context").status_code == 404
    assert api_client.get("/ai-export/route-import/download/prompt").status_code == 404


def test_path_traversal_is_not_exposed(api_client):
    response = api_client.post("/ai-export/../escape")
    assert response.status_code in {404, 400}
    assert "C:\\" not in response.text
