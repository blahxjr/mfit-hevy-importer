from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.agents.review_agent import ReviewAgent
from src.domain.models import Base, ExerciseMapping, ExerciseTemplate, ExerciseTemplateMedia, Import, SourceExercise, SourceWorkout


def test_visual_descriptor_prefers_official_then_local_then_placeholder():
    template = ExerciseTemplate(id="template-1", title="Lat Pulldown", type="strength", primary_muscle_group="back", equipment="cable")
    official = ExerciseTemplateMedia(
        template_id="template-1",
        source="hevy_official",
        image_url="https://example.com/lat.jpg",
        alt_text="Imagem de referência para Lat Pulldown",
        is_verified=True,
    )
    assert official.template_id == "template-1"
    assert template.title == "Lat Pulldown"

    local = ExerciseTemplateMedia(
        template_id="template-2",
        source="local_manual",
        image_url="/static/local/lat.jpg",
        alt_text="Imagem local de referência",
        is_verified=False,
    )
    assert local.source == "local_manual"

    placeholder_template = ExerciseTemplate(id="template-3", title="Triceps Press", type="strength", primary_muscle_group="arms", equipment="bodyweight")
    descriptor = {
        "template_id": placeholder_template.id,
        "kind": "placeholder",
        "image_url": None,
        "local_image_url": None,
        "alt_text": "Imagem de referência para Triceps Press",
        "movement_icon": "dumbbell",
        "muscle_label": "Arms",
        "equipment_label": "Bodyweight",
        "is_verified": False,
    }
    assert descriptor["kind"] == "placeholder"
    assert descriptor["image_url"] is None


def test_review_agent_includes_visual_placeholder_when_template_is_unset():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    imported = Import(id="import-1", filename="ficha.pdf", sha256="a" * 64, status="mapped")
    workout = SourceWorkout(import_ref=imported, source_name="A - Costas", order=0)
    exercise = SourceExercise(workout_ref=workout, source_name="Puxada", order=0, sets_raw="4x15")
    session.add_all([imported, workout, exercise])
    session.commit()

    review = ReviewAgent(session).generate_review(imported.id)
    assert review["workouts"][0]["exercises"][0]["mapping"]["template_visual"]["kind"] == "placeholder"
    session.close()
    engine.dispose()
