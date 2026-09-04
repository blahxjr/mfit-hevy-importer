import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.agents.mfit_parser_agent import MFITParserAgent
from src.infrastructure.database import SessionLocal, init_db

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python scripts/parse_mfit.py <arquivo.pdf>")
    init_db()
    with SessionLocal() as db:
        print(MFITParserAgent(db).parse_and_save(sys.argv[1]))
