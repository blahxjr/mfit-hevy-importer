from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.main import app
from src.domain.models import Base, ExerciseMapping, ExerciseTemplate, Import, SourceExercise, SourceWorkout
from src.infrastructure.database import get_db


def test_review_routes_show_review_and_reject_unconfirmed_plan():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    session = sessionmaker(bind=engine)()
    Base.metadata.create_all(engine)
    template = ExerciseTemplate(id="template-1", title="Lat Pulldown")
    imported = Import(id="route-import", filename="ficha.pdf", sha256="b" * 64)
    workout = SourceWorkout(import_ref=imported, source_name="A", order=0)
    exercise = SourceExercise(workout_ref=workout, source_name="Puxada", order=0)
    mapping = ExerciseMapping(source_name="Puxada", template=template, method="alias", confidence=0.95)
    session.add_all([template, imported, workout, exercise, mapping])
    session.commit()

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            review = client.get(f"/review/{imported.id}")
            approval = client.post(f"/review/{imported.id}/approve")
            workout_approval = client.post(f"/review/{imported.id}/workouts/0/approve")
        assert review.status_code == 200
        assert review.json()["summary"]["needs_review_count"] == 1
        assert approval.status_code == 409
        assert workout_approval.status_code == 409
    finally:
        app.dependency_overrides.clear()
        session.close()
        engine.dispose()


def test_workout_approval_route_approves_only_requested_workout():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    session = sessionmaker(bind=engine)()
    Base.metadata.create_all(engine)
    template = ExerciseTemplate(id="template-1", title="Lat Pulldown")
    imported = Import(id="granular-import", filename="ficha.pdf", sha256="d" * 64, status="mapped")
    first = SourceWorkout(import_ref=imported, source_name="A", order=0)
    second = SourceWorkout(import_ref=imported, source_name="B", order=1)
    source = SourceExercise(workout_ref=first, source_name="Puxada", order=0)
    mapping = ExerciseMapping(
        source_name="Puxada", template=template, method="manual", confidence=1, confirmed_by_user=True
    )
    session.add_all([template, imported, first, second, source, mapping])
    session.commit()

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            response = client.post(f"/review/{imported.id}/workouts/0/approve")
        assert response.status_code == 200
        assert first.status == "approved" and second.status == "pending"
        assert imported.status == "mapped"
    finally:
        app.dependency_overrides.clear()
        session.close()
        engine.dispose()
