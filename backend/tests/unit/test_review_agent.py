from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.agents.review_agent import ReviewAgent
from src.domain.models import Base, ExerciseMapping, ExerciseTemplate, Import, SourceExercise, SourceWorkout


def build_review_data(session, confirmed=False):
    template = ExerciseTemplate(id="template-1", title="Lat Pulldown")
    imported = Import(id="import-1", filename="ficha.pdf", sha256="a" * 64, status="mapped")
    workout = SourceWorkout(import_ref=imported, source_name="A - Costas", order=0)
    exercise = SourceExercise(workout_ref=workout, source_name="Puxada", order=0, sets_raw="4x15")
    mapping = ExerciseMapping(
        source_name="Puxada", template=template, method="alias", confidence=0.95, confirmed_by_user=confirmed
    )
    session.add_all([template, imported, workout, exercise, mapping])
    session.commit()
    return imported


def test_review_reports_pending_mapping_and_blocks_approval():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    imported = build_review_data(session)
    review = ReviewAgent(session).generate_review(imported.id)
    blocked = ReviewAgent(session).approve_workout(imported.id, 0)
    assert review["summary"] == {"total_exercises": 1, "mapped_count": 1, "needs_review_count": 1, "no_match_count": 0}
    assert blocked["error"] == "All workout mappings must be confirmed"
    session.close()
    engine.dispose()


def test_approval_updates_import_after_all_mappings_are_confirmed():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    imported = build_review_data(session, confirmed=True)
    approved = ReviewAgent(session).approve_workout(imported.id, 0)
    assert approved == {"success": True, "import_id": imported.id, "workout_order": 0, "status": "approved"}
    assert imported.status == "approved"
    session.close()
    engine.dispose()


def test_approving_a_leaves_b_and_import_pending():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    imported = build_review_data(session, confirmed=True)
    session.add(SourceWorkout(import_ref=imported, source_name="B - Pernas", order=1))
    session.commit()
    result = ReviewAgent(session).approve_workout(imported.id, 0)
    workouts = sorted(imported.workouts, key=lambda item: item.order)
    assert result["success"]
    assert [workout.status for workout in workouts] == ["approved", "pending"]
    assert imported.status == "mapped"
    session.close()
    engine.dispose()
