from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.main import app
from src.domain.models import Base, Import
from src.infrastructure.database import get_db


def test_write_routes_reject_unapproved_import_and_return_qa():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    session = sessionmaker(bind=engine)()
    Base.metadata.create_all(engine)
    imported = Import(id="write-import", filename="ficha.pdf", sha256="c" * 64, status="mapped")
    session.add(imported)
    session.commit()

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            build = client.post(f"/write/{imported.id}/build")
            execute = client.post(f"/write/{imported.id}/execute", params={"workout_order": 0})
            qa = client.post(f"/write/{imported.id}/qa")
        assert build.status_code == 409
        assert execute.status_code == 409
        assert qa.status_code == 200
        assert qa.json()["all_passed"] is False
    finally:
        app.dependency_overrides.clear()
        session.close()
        engine.dispose()
