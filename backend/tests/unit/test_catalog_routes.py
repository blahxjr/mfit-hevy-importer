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
        assert search_response.json() == {
            "templates": [
                {
                    "id": "template-2",
                    "title": "Remada Curvada",
                    "type": "strength",
                    "primary_muscle_group": None,
                    "equipment": None,
                    "is_custom": False,
                }
            ],
            "query": "remada",
            "count": 1,
        }
    finally:
        app.dependency_overrides.clear()
        session.close()
        engine.dispose()


def test_search_templates_is_local_case_insensitive_accent_aware_and_limited():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session = sessionmaker(bind=engine)()
    Base.metadata.create_all(bind=engine)
    session.add_all(
        [
            ExerciseTemplate(id="lat-1", title="Neutral Grip Lat Pulldown", type="strength", equipment="cable"),
            ExerciseTemplate(id="lat-2", title="Machine Lat Pulldown", type="strength", equipment="machine"),
            ExerciseTemplate(id="lat-3", title="Close Grip Pulldown", type="strength", equipment="cable"),
            ExerciseTemplate(id="accent", title="Puxada Articulada Neutra", type="strength"),
        ]
    )
    session.commit()

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            response = client.get("/catalog/templates/search", params={"q": "LAT PULLDOWN", "limit": 2})
            partial = client.get("/catalog/templates/search", params={"q": "pulldown"})
            accent = client.get("/catalog/templates/search", params={"q": "Puxada Articulada Neutra"})
            empty = client.get("/catalog/templates/search", params={"q": "zzzz-no-match"})
        assert response.status_code == 200
        assert response.json()["count"] == 2
        assert response.json()["templates"][0]["title"] == "Neutral Grip Lat Pulldown"
        assert len(partial.json()["templates"]) == 3
        assert accent.json()["templates"][0]["id"] == "accent"
        assert empty.json() == {"templates": [], "query": "zzzz-no-match", "count": 0}
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
