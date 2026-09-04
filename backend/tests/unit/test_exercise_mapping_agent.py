from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.agents.exercise_mapping_agent import ExerciseMappingAgent
from src.domain.models import (
    Base,
    ExerciseMapping,
    ExerciseTemplate,
    Import,
    NormalizedExercise,
    SourceExercise,
    SourceWorkout,
)


def test_map_import_is_idempotent_and_manual_confirmation_is_persisted():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    template = ExerciseTemplate(id="lat-pulldown", title="Lat Pulldown")
    imported = Import(id="import-1", filename="ficha.pdf", sha256="a" * 64)
    workout = SourceWorkout(import_ref=imported, source_name="A", order=0)
    source = SourceExercise(workout_ref=workout, source_name="Puxada Articulada Neutra", order=0)
    normalized = NormalizedExercise(source_exercise=source, sets_min=4, sets_max=4, reps_min=15, reps_max=15)
    session.add_all([template, imported, workout, source, normalized])
    session.commit()

    agent = ExerciseMappingAgent(session)
    result = agent.map_import(imported.id)
    repeated = agent.map_import(imported.id)
    mapping = session.query(ExerciseMapping).one()

    assert result["mapped_count"] == repeated["mapped_count"] == 1
    assert result["mappings"][0]["method"] == "alias"
    assert session.query(ExerciseMapping).count() == 1
    assert agent.confirm_mapping(mapping.id, template.id)["success"]
    assert mapping.confirmed_by_user and mapping.method == "manual"
    session.close()
    engine.dispose()
