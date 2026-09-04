"""Sincroniza manualmente o cache local do catálogo Hevy."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.agents.hevy_catalog_agent import HevyCatalogAgent
from src.infrastructure.database import SessionLocal, init_db


def main() -> int:
    init_db()
    with SessionLocal() as db:
        result = HevyCatalogAgent(db).sync_all()
    print(f"Templates sincronizados: {result['templates_synced']}")
    print(f"Folders sincronizados: {result['folders_synced']}")
    print(f"Rotinas sincronizadas: {result['routines_synced']}")
    if result["errors"]:
        print("Erros:")
        for error in result["errors"]:
            print(f"  - {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
