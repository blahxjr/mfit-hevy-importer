import json

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.domain.models import Base, ExerciseTemplate
from src.exercise_db.client import ExerciseDbClient
from src.exercise_db.schemas import ExerciseDbExercise
from src.repositories.exercise_repository import ExerciseRepository


def test_exercisedb_schema_accepts_legacy_and_v2_fields():
    item = ExerciseDbExercise.from_api({"id": "1", "name": "Bench Press", "bodyPart": "chest", "gifUrl": "https://example/gif"})
    assert item.external_id == "1"
    assert item.gif_url.endswith("gif")


def test_repository_upsert_search_and_link():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        repo = ExerciseRepository(db)
        item = ExerciseDbExercise.from_api({"exerciseId": "ex-1", "name": "Bench Press", "target": "pectorals", "instructions": ["Press"]})
        exercise = repo.upsert_from_exercisedb(item)
        db.commit()
        assert repo.get_by_exercisedb_id("ex-1").id == exercise.id
        assert repo.search(name="bench")[0].name == "Bench Press"
        db.add(ExerciseTemplate(id="hevy-1", title="Bench Press"))
        db.commit()
        repo.link_to_hevy_template(exercise.id, "hevy-1")
        db.commit()
        assert repo.get_by_hevy_template_id("hevy-1").id == exercise.id
