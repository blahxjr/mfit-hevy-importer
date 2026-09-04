import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.agents.workout_normalizer_agent import WorkoutNormalizerAgent
from src.infrastructure.database import SessionLocal

if len(sys.argv) != 2:
    raise SystemExit("Uso: python scripts/normalize_import.py <import_id>")
with SessionLocal() as db:
    print(WorkoutNormalizerAgent(db).normalize_import(sys.argv[1]))
