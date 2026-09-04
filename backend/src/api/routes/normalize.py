from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.agents.workout_normalizer_agent import WorkoutNormalizerAgent
from src.domain.models import NormalizedExercise, SourceExercise, SourceWorkout
from src.infrastructure.database import get_db

router = APIRouter(prefix="/normalize", tags=["Normalize"])


@router.post("/{import_id}")
def normalize_import(import_id: str, db: Session = Depends(get_db)):
    result = WorkoutNormalizerAgent(db).normalize_import(import_id)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return result


@router.get("/{import_id}/exercises")
def exercises(import_id: str, db: Session = Depends(get_db)):
    rows = db.scalars(
        select(NormalizedExercise).join(SourceExercise).join(SourceWorkout).where(SourceWorkout.import_id == import_id)
    ).all()
    return {
        "exercises": [
            {
                "id": x.id,
                "source_name": x.source_exercise.source_name,
                "sets_min": x.sets_min,
                "sets_max": x.sets_max,
                "reps_min": x.reps_min,
                "reps_max": x.reps_max,
                "load_value": x.load_value,
                "load_unit": x.load_unit,
                "rest_seconds": x.rest_seconds,
                "is_timed": x.is_timed,
                "needs_review": x.needs_review,
                "review_reason": x.review_reason,
                "confidence": x.confidence,
            }
            for x in rows
        ]
    }
