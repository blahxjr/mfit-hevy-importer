from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.agents.review_agent import ReviewAgent
from src.infrastructure.database import get_db

router = APIRouter(prefix="/review", tags=["Review"])


@router.get("/{import_id}")
def get_review(import_id: str, db: Session = Depends(get_db)):
    result = ReviewAgent(db).generate_review(import_id)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return result


@router.post("/{import_id}/approve")
def approve_plan(import_id: str, db: Session = Depends(get_db)):
    result = ReviewAgent(db).approve_plan(import_id)
    if "error" in result:
        status = 404 if result["error"] == "Import not found" else 409
        raise HTTPException(status, result)
    return result


@router.post("/{import_id}/workouts/{workout_order}/approve")
def approve_workout(import_id: str, workout_order: int, db: Session = Depends(get_db)):
    result = ReviewAgent(db).approve_workout(import_id, workout_order)
    if "error" in result:
        raise HTTPException(404 if result["error"] == "Workout not found" else 409, result)
    return result
