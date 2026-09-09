"""Gera localmente o pacote de prompt e contexto para IA externa."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.agents.ai_export_agent import AIExportAgent, AIExportError
from src.infrastructure.database import SessionLocal, init_db


def main() -> int:
    parser = argparse.ArgumentParser(description="Exporta contexto MFIT para canonicalização manual")
    parser.add_argument("import_id")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        result = AIExportAgent(db).export_import_for_external_ai(args.import_id)
    except AIExportError as error:
        print(f"erro: {error}")
        return 1
    finally:
        db.close()

    print(f"import_id: {result['import_id']}")
    print(f"status: {result['status']}")
    print(f"prompt_filename: {result['prompt_filename']}")
    print(f"context_filename: {result['context_filename']}")
    print(f"workouts_count: {result['workouts_count']}")
    print(f"exercises_count: {result['exercises_count']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
