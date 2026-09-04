import re
from dataclasses import dataclass


@dataclass
class NormalizedExerciseData:
    sets_min: int | None = None
    sets_max: int | None = None
    reps_min: int | None = None
    reps_max: int | None = None
    load_value: float | None = None
    load_unit: str | None = None
    rest_seconds: int | None = None
    is_timed: bool = False
    duration_seconds: int | None = None
    sets_raw: str | None = None
    reps_raw: str | None = None
    load_raw: str | None = None
    rest_raw: str | None = None
    needs_review: bool = False
    review_reason: str | None = None
    confidence: float = 1.0


class WorkoutNormalizer:
    def normalize_sets_reps(self, sets_raw, reps_raw=None):
        result = NormalizedExerciseData(sets_raw=sets_raw, reps_raw=reps_raw)
        value = (sets_raw or "").lower().replace(" ", "")
        timed = re.match(r"^(\d+)x(\d+)(s|seg)$", value)
        reps = re.match(r"^(\d+)x(\d+)(?:-(\d+))?$", value)
        if timed:
            result.sets_min = result.sets_max = int(timed[1])
            result.is_timed = True
            result.duration_seconds = int(timed[2])
            return result
        if reps:
            result.sets_min = result.sets_max = int(reps[1])
            result.reps_min = int(reps[2])
            result.reps_max = int(reps[3] or reps[2])
            return result
        result.needs_review = True
        result.review_reason = f"Could not parse sets_raw: {sets_raw}"
        result.confidence = 0.5
        return result

    def normalize_load(self, raw):
        value = (raw or "").strip().lower()
        if not value:
            return None, None, False, None
        if "corporal" in value or "bodyweight" in value:
            return None, None, True, "bodyweight_exercise"
        match = re.fullmatch(r"([\d.,]+)\s*(kg|lb)", value)
        return (
            (float(match[1].replace(",", ".")), match[2], False, None)
            if match
            else (None, None, True, f"Could not parse load_raw: {raw}")
        )

    def normalize_rest(self, raw):
        value = (raw or "").strip().lower()
        if not value:
            return None, False, None
        if match := re.fullmatch(r"(\d+)\s*(?:s|seg)?", value):
            return int(match[1]), False, None
        if match := re.fullmatch(r"(\d+)\s*min(?:utos?)?", value):
            return int(match[1]) * 60, False, None
        if match := re.fullmatch(r"(\d+):(\d+)", value):
            return int(match[1]) * 60 + int(match[2]), False, None
        return None, True, f"Could not parse rest_raw: {raw}"
