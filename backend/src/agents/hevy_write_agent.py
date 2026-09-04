"""Executa operações aprovadas e persiste somente rotinas criadas com sucesso."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.models import Routine, SourceWorkout
from src.hevy.client import HevyClient
from src.repositories.import_repository import ImportRepository


class HevyWriteAgent:
    def __init__(self, db: Session, client: HevyClient | None = None) -> None:
        self.db, self.client, self.import_repo = db, client or HevyClient(), ImportRepository(db)

    def execute_operation(self, operation: dict) -> dict:
        try:
            response = self.client.post(operation["endpoint"], operation["payload"], operation["idempotency_key"])
            routine = response.get("routine", response)
            return {
                "operation_id": operation["operation_id"],
                "success": True,
                "remote_id": routine.get("id"),
                "status_code": 200,
            }
        except Exception as exc:
            status = getattr(getattr(exc, "response", None), "status_code", 0)
            return {
                "operation_id": operation["operation_id"],
                "success": False,
                "status_code": status,
                "error": str(exc),
            }

    def execute_plan(self, import_id: str, operations: list[dict]) -> dict:
        imported = self.import_repo.get_by_id(import_id)
        if not imported:
            return {
                "import_id": import_id,
                "error": "Import not found",
                "results": [],
                "success_count": 0,
                "failure_count": 0,
            }
        workout_orders = {operation.get("workout_order") for operation in operations}
        if len(operations) != 1 or len(workout_orders) != 1 or None in workout_orders:
            return {
                "import_id": import_id,
                "error": "Exactly one workout operation is required",
                "results": [],
                "success_count": 0,
                "failure_count": 0,
            }
        workout_order = workout_orders.pop()
        workout = self.db.scalar(
            select(SourceWorkout).where(SourceWorkout.import_id == import_id, SourceWorkout.order == workout_order)
        )
        if not workout or workout.status != "approved":
            return {
                "import_id": import_id,
                "error": "Workout not approved",
                "results": [],
                "success_count": 0,
                "failure_count": 0,
            }
        workout.status = "writing"
        self.db.commit()
        results = [self.execute_operation(operation) for operation in operations]
        for operation, result in zip(operations, results):
            if result["success"] and result.get("remote_id") and not self.db.get(Routine, result["remote_id"]):
                self.db.add(
                    Routine(
                        id=result["remote_id"],
                        title=operation["payload"]["title"],
                        folder_id=operation["payload"].get("folder_id"),
                    )
                )
        failures = sum(not result["success"] for result in results)
        workout.status = "completed" if not failures else "failed"
        all_workouts = self.db.scalars(select(SourceWorkout).where(SourceWorkout.import_id == import_id)).all()
        if failures:
            imported.status = "failed"
        elif all(item.status == "completed" for item in all_workouts):
            imported.status = "completed"
        self.db.commit()
        return {
            "import_id": import_id,
            "results": results,
            "success_count": len(results) - failures,
            "failure_count": failures,
        }
