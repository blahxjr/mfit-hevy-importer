import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.agents.hevy_write_agent import HevyWriteAgent
from src.agents.payload_builder_agent import PayloadBuilderAgent
from src.infrastructure.database import SessionLocal

parser = argparse.ArgumentParser(description="Executa uma única rotina aprovada no Hevy.")
parser.add_argument("import_id")
parser.add_argument("--workout-order", type=int, required=True)
parser.add_argument("--confirm-write", action="store_true")
arguments = parser.parse_args()
if not arguments.confirm_write:
    raise SystemExit("Escrita bloqueada: informe --confirm-write após revisar o dry-run.")
with SessionLocal() as db:
    plan = PayloadBuilderAgent(db).build_payload(arguments.import_id, workout_order=arguments.workout_order)
    if plan.get("blocked"):
        raise SystemExit("Plano bloqueado: revise e confirme todos os mapeamentos antes da escrita.")
    print(HevyWriteAgent(db).execute_plan(sys.argv[1], plan["operations"]))
