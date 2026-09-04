from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.models import Import, Routine


class QAAgent:
    def __init__(self, db: Session):
        self.db = db

    def verify_import(self, import_id: str) -> dict:
        imported = self.db.get(Import, import_id)
        if not imported:
            return {"import_id": import_id, "status": "not_found", "checks": [], "all_passed": False}
        routines = self.db.scalar(select(Routine).limit(1)) is not None
        checks = [
            {
                "name": "Import status is completed",
                "passed": imported.status == "completed",
                "message": f"Status: {imported.status}",
            },
            {"name": "Routines created", "passed": routines, "message": "At least one cached routine exists"},
        ]
        return {
            "import_id": import_id,
            "status": imported.status,
            "checks": checks,
            "all_passed": all(item["passed"] for item in checks),
        }
