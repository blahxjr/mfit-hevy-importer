"""Endpoints do catálogo próprio de exercícios."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.agents.exercise_catalog_agent import ExerciseCatalogAgent
from src.infrastructure.database import get_db

router = APIRouter(prefix="/catalog/exercises", tags=["Exercise catalog"])


def dto(item) -> dict[str, object]:
    return {"id": item.id, "exercisedb_id": item.exercisedb_id, "hevy_template_id": item.hevy_template_id,
            "name": item.name, "name_en": item.name_en, "body_part": item.body_part, "target_muscle": item.target_muscle,
            "secondary_muscles": __import__("json").loads(item.secondary_muscles or "[]"), "equipment": item.equipment,
            "movement_pattern": item.movement_pattern, "instructions": item.instructions, "image_url": item.image_url,
            "video_url": item.video_url, "media_hint": item.media_hint, "source": item.source}


@router.get("")
def list_exercises(q: str | None = Query(None), body_part: str | None = None, target: str | None = None,
                   equipment: str | None = None, movement_pattern: str | None = None, source: str | None = None,
                   linked: bool | None = None, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0),
                   db: Session = Depends(get_db)) -> dict[str, object]:
    items = ExerciseCatalogAgent(db).list(name=q, body_part=body_part, target=target, equipment=equipment,
                                           movement_pattern_filter=movement_pattern, source=source, linked=linked,
                                           limit=limit, offset=offset)
    return {"exercises": [dto(item) for item in items], "count": len(items), "offset": offset, "limit": limit}


@router.get("/{exercise_id}")
def get_exercise(exercise_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    item = ExerciseCatalogAgent(db).get(exercise_id)
    if item is None:
        raise HTTPException(404, "Exercise not found")
    return dto(item)


@router.post("/sync")
def sync_exercises(db: Session = Depends(get_db)) -> dict[str, object]:
    result = ExerciseCatalogAgent(db).sync()
    if result.get("errors"):
        raise HTTPException(502, result)
    return result