from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.agents.hevy_write_agent import HevyWriteAgent
from src.agents.payload_builder_agent import PayloadBuilderAgent
from src.agents.qa_agent import QAAgent
from src.infrastructure.database import get_db

router = APIRouter(prefix="/write", tags=["Write"])


@router.post("/{import_id}/build")
def build(
    import_id: str,
    folder_id: int | None = None,
    workout_order: int | None = None,
    db: Session = Depends(get_db),
):
    result = PayloadBuilderAgent(db).build_payload(import_id, folder_id, workout_order)
    if "error" in result:
        raise HTTPException(404 if result["error"] == "Import not found" else 409, result)
    return result


@router.post("/{import_id}/execute")
def execute(import_id: str, workout_order: int, db: Session = Depends(get_db)):
    plan = PayloadBuilderAgent(db).build_payload(import_id, workout_order=workout_order)
    if plan.get("blocked"):
        raise HTTPException(409, "Plan is blocked. Review and confirm all mappings.")
    if "error" in plan:
        raise HTTPException(404, plan["error"])
    return HevyWriteAgent(db).execute_plan(import_id, plan["operations"])


@router.post("/{import_id}/qa")
def qa(import_id: str, db: Session = Depends(get_db)):
    return QAAgent(db).verify_import(import_id)
