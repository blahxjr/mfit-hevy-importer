"""Contratos tolerantes para as versões pública v1/v2 da ExerciseDB."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExerciseDbExercise(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    external_id: str = Field(alias="exerciseId")
    name: str
    body_part: str | None = Field(None, alias="bodyPart")
    target: str | None = None
    equipment: str | None = None
    secondary_muscles: list[str] = Field(default_factory=list, alias="secondaryMuscles")
    instructions: list[str] = Field(default_factory=list)
    image_url: str | None = Field(None, alias="imageUrl")
    gif_url: str | None = Field(None, alias="gifUrl")
    video_url: str | None = Field(None, alias="videoUrl")

    @field_validator("external_id", mode="before")
    @classmethod
    def accept_legacy_id(cls, value: Any) -> str:
        return str(value)

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> "ExerciseDbExercise":
        data = dict(payload)
        if "exerciseId" not in data and "id" in data:
            data["exerciseId"] = data["id"]
        if "imageUrl" not in data and "image" in data:
            data["imageUrl"] = data["image"]
        return cls.model_validate(data)


class ExerciseDbPage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    items: list[ExerciseDbExercise] = Field(default_factory=list)
    page: int = 1
    limit: int = 0
    total: int | None = None