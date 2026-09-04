from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.agents.exercise_mapping_agent import ExerciseMappingAgent
from src.domain.models import ExerciseTemplate
from src.infrastructure.database import get_db
from src.parsers.exercise_mapper import ExerciseMapper

router = APIRouter(prefix="/mapping", tags=["Mapping"])


@router.post("/{import_id}/map")
def map_import(import_id: str, db: Session = Depends(get_db)):
    return ExerciseMappingAgent(db).map_import(import_id)


@router.post("/{mapping_id}/confirm")
def confirm(mapping_id: int, template_id: str, db: Session = Depends(get_db)):
    r = ExerciseMappingAgent(db).confirm_mapping(mapping_id, template_id)
    if "error" in r:
        raise HTTPException(404, r["error"])
    return r


@router.get("/alternatives/{source_name}")
def alternatives(source_name: str, db: Session = Depends(get_db)):
    return {
        "alternatives": [
            x.__dict__
            for x in ExerciseMapper(
                [{"id": t.id, "title": t.title} for t in db.query(ExerciseTemplate)]
            ).get_alternatives(source_name)
        ]
    }
