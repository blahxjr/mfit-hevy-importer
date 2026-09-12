"""Persistência e busca do catálogo próprio de exercícios."""

import json
import uuid
import unicodedata

from rapidfuzz import fuzz
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from src.domain.models import Exercise
from src.exercise_db.schemas import ExerciseDbExercise
from src.exercise_db.service import movement_pattern


class ExerciseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, exercise_id: str) -> Exercise | None:
        return self.db.get(Exercise, exercise_id)

    def get_by_exercisedb_id(self, external_id: str) -> Exercise | None:
        return self.db.scalar(select(Exercise).where(Exercise.exercisedb_id == external_id))

    def get_by_hevy_template_id(self, template_id: str) -> Exercise | None:
        return self.db.scalar(select(Exercise).where(Exercise.hevy_template_id == template_id))

    def search(self, *, name: str | None = None, body_part: str | None = None, target: str | None = None,
               equipment: str | None = None, movement_pattern_filter: str | None = None,
               source: str | None = None, linked: bool | None = None, limit: int = 50, offset: int = 0) -> list[Exercise]:
        query = select(Exercise)
        if name:
            query = query.where(or_(Exercise.name.ilike(f"%{name}%"), Exercise.name_en.ilike(f"%{name}%")))
        for column, value in ((Exercise.body_part, body_part), (Exercise.target_muscle, target), (Exercise.equipment, equipment)):
            if value:
                query = query.where(column.ilike(f"%{value}%"))
        if movement_pattern_filter:
            query = query.where(Exercise.movement_pattern == movement_pattern_filter)
        if source:
            query = query.where(Exercise.source == source)
        if linked is True:
            query = query.where(Exercise.hevy_template_id.is_not(None))
        elif linked is False:
            query = query.where(Exercise.hevy_template_id.is_(None))
        return list(self.db.scalars(query.order_by(Exercise.name).offset(offset).limit(min(limit, 100))))

    def upsert_from_exercisedb(self, item: ExerciseDbExercise) -> Exercise:
        entity = self.get_by_exercisedb_id(item.external_id)
        if entity is None:
            entity = Exercise(id=str(uuid.uuid4()), exercisedb_id=item.external_id, name=item.name, source="exercisedb")
            self.db.add(entity)
        entity.name = item.name
        entity.name_en = item.name
        entity.body_part = item.body_part
        entity.target_muscle = item.target
        entity.secondary_muscles = json.dumps(item.secondary_muscles, ensure_ascii=False)
        entity.equipment = item.equipment
        entity.movement_pattern = movement_pattern(item)
        entity.instructions = "\n".join(item.instructions) or None
        entity.image_url = item.image_url or item.gif_url
        entity.video_url = item.video_url
        entity.media_hint = "video" if item.video_url else "image" if entity.image_url else None
        return entity

    def link_to_hevy_template(self, exercise_id: str, template_id: str) -> Exercise:
        entity = self.get_by_id(exercise_id)
        if entity is None:
            raise ValueError("Exercise not found")
        entity.hevy_template_id = template_id
        return entity


def normalize_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.lower())
    return " ".join("".join(c for c in value if not unicodedata.combining(c)).split())


def rank_name(query: str, candidate: str) -> float:
    return fuzz.WRatio(normalize_name(query), normalize_name(candidate)) / 100