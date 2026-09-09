"""Modelos estritos para respostas de canonicalização geradas externamente."""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ExternalAIProvider(str, Enum):
    chatgpt = "chatgpt"
    perplexity = "perplexity"
    copilot = "copilot"
    grok = "grok"
    deepseek = "deepseek"
    gemini = "gemini"
    claude = "claude"
    ollama = "ollama"
    other = "other"


class MovementPattern(str, Enum):
    horizontal_push = "horizontal_push"
    vertical_push = "vertical_push"
    horizontal_pull = "horizontal_pull"
    vertical_pull = "vertical_pull"
    squat = "squat"
    hip_hinge = "hip_hinge"
    lunge = "lunge"
    knee_extension = "knee_extension"
    knee_flexion = "knee_flexion"
    calf_raise = "calf_raise"
    core = "core"
    cardio = "cardio"
    mobility = "mobility"
    other = "other"


class EquipmentHint(str, Enum):
    barbell = "barbell"
    dumbbell = "dumbbell"
    cable = "cable"
    machine = "machine"
    bodyweight = "bodyweight"
    smith_machine = "smith_machine"
    kettlebell = "kettlebell"
    resistance_band = "resistance_band"
    plate = "plate"
    other = "other"


class StrictExternalAIModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ExternalAIGeneratedBy(StrictExternalAIModel):
    provider: ExternalAIProvider
    model: str | None = Field(default=None, max_length=120)
    generated_at: datetime | None = None


class ExternalAIExerciseResponse(StrictExternalAIModel):
    source_exercise_id: int = Field(gt=0)
    source_exercise_order: int = Field(ge=0)
    source_name_pt: str = Field(min_length=1, max_length=250)
    canonical_name_en: str | None = Field(default=None, max_length=250)
    search_aliases_en: list[str] = Field(default_factory=list, max_length=5)
    movement_pattern: MovementPattern | None = None
    equipment_hint: EquipmentHint | None = None
    primary_muscle_hint: str | None = Field(default=None, max_length=100)
    secondary_muscles_hint: list[str] = Field(default_factory=list, max_length=8)
    confidence: float = Field(ge=0, le=1)
    needs_review: bool
    review_reason: str | None = Field(default=None, max_length=1000)
    notes_for_hevy_search: str | None = Field(default=None, max_length=1000)


class ExternalAIWorkoutResponse(StrictExternalAIModel):
    source_workout_order: int = Field(ge=0)
    source_workout_name_pt: str = Field(min_length=1, max_length=250)
    exercises: list[ExternalAIExerciseResponse] = Field(min_length=1)


class ExternalAIResponse(StrictExternalAIModel):
    schema_version: Literal["1.0"]
    import_id: str = Field(min_length=1, max_length=100)
    source_filename: str = Field(min_length=1, max_length=500)
    generated_by: ExternalAIGeneratedBy
    workouts: list[ExternalAIWorkoutResponse] = Field(min_length=1)
