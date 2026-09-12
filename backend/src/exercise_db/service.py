"""Normalização de dados recebidos da ExerciseDB."""

from src.exercise_db.schemas import ExerciseDbExercise


def movement_pattern(exercise: ExerciseDbExercise) -> str | None:
    text = " ".join(filter(None, [exercise.name, exercise.target, exercise.equipment])).lower()
    for pattern, words in (("squat", ("squat", "leg press", "lunge")), ("hinge", ("deadlift", "good morning", "hip thrust")),
                           ("push", ("press", "push", "fly", "extension")), ("pull", ("row", "pull", "curl")),
                           ("core", ("plank", "crunch", "abdominal"))):
        if any(word in text for word in words):
            return pattern
    return None