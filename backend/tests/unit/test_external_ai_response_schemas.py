import pytest
from pydantic import ValidationError

from src.schemas.external_ai_response import ExternalAIResponse


def valid_payload():
    return {
        "schema_version": "1.0",
        "import_id": "schema-import",
        "source_filename": "ficha.pdf",
        "generated_by": {"provider": "chatgpt", "model": "test"},
        "workouts": [
            {
                "source_workout_order": 0,
                "source_workout_name_pt": "A - Peito",
                "exercises": [
                    {
                        "source_exercise_id": 1,
                        "source_exercise_order": 0,
                        "source_name_pt": "Supino",
                        "canonical_name_en": "Bench Press",
                        "search_aliases_en": [],
                        "movement_pattern": "horizontal_push",
                        "equipment_hint": "barbell",
                        "primary_muscle_hint": "chest",
                        "secondary_muscles_hint": [],
                        "confidence": 0.8,
                        "needs_review": False,
                        "review_reason": None,
                        "notes_for_hevy_search": None,
                    }
                ],
            }
        ],
    }


def test_valid_payload():
    assert ExternalAIResponse.model_validate(valid_payload()).import_id == "schema-import"


@pytest.mark.parametrize("field", ["template_id", "api_key", "routine_id"])
def test_forbidden_extra_fields_are_rejected(field):
    payload = valid_payload()
    payload[field] = "forbidden"
    with pytest.raises(ValidationError):
        ExternalAIResponse.model_validate(payload)


def test_bounds_and_enums_are_rejected():
    payload = valid_payload()
    payload["workouts"][0]["exercises"][0]["confidence"] = 1.1
    with pytest.raises(ValidationError):
        ExternalAIResponse.model_validate(payload)
    payload = valid_payload()
    payload["workouts"][0]["exercises"][0]["movement_pattern"] = "unknown"
    with pytest.raises(ValidationError):
        ExternalAIResponse.model_validate(payload)


def test_alias_and_muscle_limits_are_rejected():
    payload = valid_payload()
    exercise = payload["workouts"][0]["exercises"][0]
    exercise["search_aliases_en"] = ["x"] * 6
    with pytest.raises(ValidationError):
        ExternalAIResponse.model_validate(payload)
    payload = valid_payload()
    payload["workouts"][0]["exercises"][0]["secondary_muscles_hint"] = ["x"] * 9
    with pytest.raises(ValidationError):
        ExternalAIResponse.model_validate(payload)
