import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.agents.payload_builder_agent import PayloadBuilderAgent
from src.infrastructure.database import SessionLocal

if len(sys.argv) != 2:
    raise SystemExit("Uso: python scripts/build_payload.py <import_id>")
with SessionLocal() as db:
    print(json.dumps(PayloadBuilderAgent(db).build_payload(sys.argv[1]), ensure_ascii=False, indent=2))
