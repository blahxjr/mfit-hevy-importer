import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.agents.exercise_mapping_agent import ExerciseMappingAgent
from src.infrastructure.database import SessionLocal

if len(sys.argv) != 2:
    raise SystemExit("Uso: python scripts/map_import.py <import_id>")
with SessionLocal() as db:
    print(ExerciseMappingAgent(db).map_import(sys.argv[1]))
