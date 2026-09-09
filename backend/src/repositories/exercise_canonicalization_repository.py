"""Persistência das sugestões de canonicalização de exercícios."""

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.models import ExerciseCanonicalization, SourceExercise, SourceWorkout
from src.repositories.base import BaseRepository


def serialize_string_list(values: list[str] | None) -> str | None:
    """Serializa uma lista de strings como JSON, sem executar conteúdo externo."""
    if values is None:
        return None
    return json.dumps(values, ensure_ascii=False)


def deserialize_string_list(value: str | None) -> list[str]:
    """Desserializa uma lista JSON legada sem propagar dados inválidos."""
    if not value:
        return []
    try:
        decoded = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return []
    return decoded if isinstance(decoded, list) and all(isinstance(item, str) for item in decoded) else []


class ExerciseCanonicalizationRepository(BaseRepository[ExerciseCanonicalization]):
    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_id(self, canonicalization_id: int) -> ExerciseCanonicalization | None:
        return self.db.scalar(
            select(ExerciseCanonicalization).where(ExerciseCanonicalization.id == canonicalization_id)
        )

    def get_by_source_exercise_id(self, source_exercise_id: int) -> ExerciseCanonicalization | None:
        return self.db.scalar(
            select(ExerciseCanonicalization).where(ExerciseCanonicalization.source_exercise_id == source_exercise_id)
        )

    def get_by_import_id(self, import_id: str) -> list[ExerciseCanonicalization]:
        statement = (
            select(ExerciseCanonicalization)
            .join(SourceExercise, SourceExercise.id == ExerciseCanonicalization.source_exercise_id)
            .join(SourceWorkout, SourceWorkout.id == SourceExercise.workout_id)
            .where(SourceWorkout.import_id == import_id)
            .order_by(SourceWorkout.order, SourceExercise.order)
        )
        return list(self.db.scalars(statement))

    def upsert(
        self,
        source_exercise_id: int,
        source_name_pt: str,
        canonical_name_en: str | None,
        search_aliases_en: list[str],
        movement_pattern: str | None,
        equipment_hint: str | None,
        primary_muscle_hint: str | None,
        secondary_muscles_hint: list[str],
        confidence: float,
        needs_review: bool,
        review_reason: str | None,
        provider: str,
        model_name: str | None,
        prompt_version: str,
        raw_response_sanitized: str | None,
    ) -> ExerciseCanonicalization:
        entity = self.get_by_source_exercise_id(source_exercise_id)
        if entity is None:
            entity = ExerciseCanonicalization(source_exercise_id=source_exercise_id)
            self.db.add(entity)

        entity.source_name_pt = source_name_pt
        entity.canonical_name_en = canonical_name_en
        entity.search_aliases_en = serialize_string_list(search_aliases_en)
        entity.movement_pattern = movement_pattern
        entity.equipment_hint = equipment_hint
        entity.primary_muscle_hint = primary_muscle_hint
        entity.secondary_muscles_hint = serialize_string_list(secondary_muscles_hint)
        entity.confidence = confidence
        entity.needs_review = needs_review
        entity.review_reason = review_reason
        entity.provider = provider
        entity.model_name = model_name
        entity.prompt_version = prompt_version
        entity.raw_response_sanitized = raw_response_sanitized

        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete_by_source_exercise_id(self, source_exercise_id: int) -> bool:
        entity = self.get_by_source_exercise_id(source_exercise_id)
        if entity is None:
            return False
        self.db.delete(entity)
        self.db.commit()
        return True
