from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.agents.mfit_parser_agent import MFITParserAgent
from src.agents.workout_normalizer_agent import WorkoutNormalizerAgent
from src.domain.models import Base, Import, SourceExercise, SourceWorkout
from src.parsers.mfit_parser import MFITParser

FIXTURE = Path(__file__).parents[1] / "fixtures" / "mfit_sample_01.pdf"


def test_parse_reference_mfit_pdf():
    parsed = MFITParser(FIXTURE).parse()
    assert parsed.pages == 5
    assert [workout.source_name[0] for workout in parsed.workouts] == ["A", "B", "C", "D", "E"]
    assert sum(len(workout.exercises) for workout in parsed.workouts) >= 30
    exercises = [exercise for workout in parsed.workouts for exercise in workout.exercises]
    assert any("8x8" in exercise.techniques for exercise in exercises)
    assert any(exercise.group_id is not None for exercise in exercises)
    assert any(exercise.reps_raw and "60s" in exercise.reps_raw for exercise in exercises)


def test_agent_saves_once_and_detects_duplicate():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    result = MFITParserAgent(session).parse_and_save(str(FIXTURE))
    duplicate = MFITParserAgent(session).parse_and_save(str(FIXTURE))
    assert result["status"] == "parsed" and result["workouts_count"] == 5
    assert result["exercises_count"] >= 30
    assert duplicate["status"] == "duplicate"
    assert session.query(Import).count() == 1
    assert session.query(SourceWorkout).count() == 5
    assert session.query(SourceExercise).count() == result["exercises_count"]
    normalized = WorkoutNormalizerAgent(session).normalize_import(result["import_id"])
    assert normalized["normalized_count"] == result["exercises_count"]
    assert session.query(SourceExercise).filter(SourceExercise.normalized.has()).count() == result["exercises_count"]
    session.close()
    engine.dispose()
