import pytest

from src.parsers.workout_normalizer import WorkoutNormalizer


@pytest.mark.parametrize("raw,sets,reps", [("4x15", 4, (15, 15)), ("4x15-20", 4, (15, 20))])
def test_reps(raw, sets, reps):
    r = WorkoutNormalizer().normalize_sets_reps(raw)
    assert (r.sets_min, r.sets_max) == (sets, sets) and (r.reps_min, r.reps_max) == reps and not r.needs_review


def test_timed():
    r = WorkoutNormalizer().normalize_sets_reps("4x30s")
    assert r.is_timed and r.duration_seconds == 30


@pytest.mark.parametrize("raw,expected", [("20kg", (20.0, "kg")), ("45 lb", (45.0, "lb"))])
def test_load(raw, expected):
    assert WorkoutNormalizer().normalize_load(raw)[:2] == expected


@pytest.mark.parametrize("raw,expected", [("60s", 60), ("2min", 120), ("1:30", 90)])
def test_rest(raw, expected):
    assert WorkoutNormalizer().normalize_rest(raw)[0] == expected


def test_ambiguous():
    r = WorkoutNormalizer().normalize_sets_reps("2x15 + 2x6")
    assert r.needs_review and r.confidence == 0.5
