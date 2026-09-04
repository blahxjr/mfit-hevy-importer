import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.agents.review_agent import ReviewAgent
from src.infrastructure.database import SessionLocal

if len(sys.argv) != 2:
    raise SystemExit("Uso: python scripts/review_import.py <import_id>")
with SessionLocal() as db:
    print(json.dumps(ReviewAgent(db).generate_review(sys.argv[1]), ensure_ascii=False, indent=2))
