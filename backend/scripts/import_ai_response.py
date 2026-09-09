"""Importa e valida uma resposta JSON de IA externa."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.agents.ai_response_import_agent import AIResponseImportAgent, AIResponseImportError
from src.infrastructure.database import SessionLocal, init_db


def main() -> int:
    parser = argparse.ArgumentParser(description="Importa resposta JSON de canonicalização")
    parser.add_argument("response_file")
    args = parser.parse_args()
    path = Path(args.response_file)
    if not path.is_file():
        print("erro: arquivo de resposta não encontrado")
        return 1
    try:
        content = path.read_bytes()
    except OSError:
        print("erro: não foi possível ler o arquivo de resposta")
        return 1

    init_db()
    db = SessionLocal()
    try:
        result = AIResponseImportAgent(db).import_external_ai_response(content, path.name)
    except AIResponseImportError as error:
        print(f"erro: {error}")
        return 1
    finally:
        db.close()

    print(f"status: {result['status']}")
    print(f"import_id: {result.get('import_id', '')}")
    print(f"provider: {result.get('provider', '')}")
    print(f"accepted_count: {result.get('accepted_count', 0)}")
    print(f"created_count: {result.get('created_count', 0)}")
    print(f"updated_count: {result.get('updated_count', 0)}")
    print(f"rejected_count: {result.get('rejected_count', 0)}")
    print(f"warnings_count: {len(result.get('warnings', []))}")
    errors = result.get("validation_report", {}).get("errors", [])
    if errors:
        print(f"error_summary: {errors[0]}")
    return 0 if result["status"] == "imported" else 1


if __name__ == "__main__":
    sys.exit(main())
