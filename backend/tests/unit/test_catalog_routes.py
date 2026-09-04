from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.main import app
from src.api.routes import catalog
from src.domain.models import Base, ExerciseTemplate
from src.infrastructure.database import get_db


def test_list_and_search_cached_templates():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session = sessionmaker(bind=engine)()
    Base.metadata.create_all(bind=engine)
    session.add_all(
        [
            ExerciseTemplate(id="template-1", title="Supino Reto", type="strength"),
            ExerciseTemplate(id="template-2", title="Remada Curvada", type="strength"),
        ]
    )
    session.commit()

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            list_response = client.get("/catalog/templates")
            search_response = client.get("/catalog/templates/search", params={"q": "remada"})

        assert list_response.status_code == 200
        assert list_response.json()["templates"] == [
            {"id": "template-2", "title": "Remada Curvada", "type": "strength"},
            {"id": "template-1", "title": "Supino Reto", "type": "strength"},
        ]
        assert search_response.status_code == 200
        assert search_response.json() == {"templates": [{"id": "template-2", "title": "Remada Curvada"}]}
    finally:
        app.dependency_overrides.clear()
        session.close()
        engine.dispose()


def test_sync_catalog_returns_agent_summary(monkeypatch):
    class FakeCatalogAgent:
        def __init__(self, db):
            self.db = db

        def sync_all(self):
            return {"templates_synced": 2, "folders_synced": 1, "routines_synced": 1, "errors": []}

    monkeypatch.setattr(catalog, "HevyCatalogAgent", FakeCatalogAgent)

    def override_get_db():
        yield object()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            response = client.post("/catalog/sync")

        assert response.status_code == 200
        assert response.json() == {"templates_synced": 2, "folders_synced": 1, "routines_synced": 1, "errors": []}
    finally:
        app.dependency_overrides.clear()
