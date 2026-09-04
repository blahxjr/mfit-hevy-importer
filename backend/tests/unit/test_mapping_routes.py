from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.main import app
from src.domain.models import Base, ExerciseMapping, ExerciseTemplate
from src.infrastructure.database import get_db


def test_mapping_alternatives_and_confirmation_routes():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    session = sessionmaker(bind=engine)()
    Base.metadata.create_all(engine)
    template = ExerciseTemplate(id="template-1", title="Lat Pulldown")
    mapping = ExerciseMapping(source_name="Puxada", method="fuzzy", confidence=0.8)
    session.add_all([template, mapping])
    session.commit()

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            alternatives = client.get("/mapping/alternatives/Lat%20Pulldown")
            confirmation = client.post(f"/mapping/{mapping.id}/confirm", params={"template_id": template.id})
        assert alternatives.status_code == 200
        assert alternatives.json()["alternatives"][0]["template_id"] == template.id
        assert confirmation.status_code == 200
        assert confirmation.json()["success"] is True
    finally:
        app.dependency_overrides.clear()
        session.close()
        engine.dispose()
