import pytest

from src.parsers.exercise_mapper import ExerciseMapper, MappingCandidate


@pytest.fixture
def mapper():
    return ExerciseMapper(
        [
            {"id": "1", "title": "Lat Pulldown"},
            {"id": "2", "title": "Bench Press"},
            {"id": "3", "title": "Leg Extension"},
        ]
    )


def test_exact(mapper):
    r = mapper.map_exercise("Lat Pulldown", {})
    assert (r.template_id, r.method, r.confidence, r.needs_review) == ("1", "exact", 1, False)


def test_alias(mapper):
    assert mapper.map_exercise("Puxada Articulada Neutra", {}).method == "alias"


def test_fuzzy(mapper):
    r = mapper.map_exercise("Lat Pulldwon", {})
    assert r.template_id == "1" and r.method == "fuzzy"
    assert 0.75 <= r.confidence < 0.92
    assert r.needs_review


def test_no_match(mapper):
    assert mapper.map_exercise("Completamente Inexistente", {}).template_id is None


def test_memory(mapper):
    r = mapper.map_exercise("qualquer", {"qualquer": MappingCandidate("2", "Bench Press", "manual", 1, False)})
    assert r.method == "memory"


def test_alternatives(mapper):
    assert mapper.get_alternatives("Lat Pulldown", 2)[0].template_id == "1"
