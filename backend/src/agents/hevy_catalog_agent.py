"""Sincroniza o catálogo de leitura do Hevy com o cache local."""

import json
from collections.abc import Callable
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.models import ExerciseTemplate, Routine, RoutineFolder
from src.hevy.client import HevyClient
from src.repositories.exercise_template_repository import ExerciseTemplateRepository
from src.repositories.routine_folder_repository import RoutineFolderRepository
from src.repositories.routine_repository import RoutineRepository


class HevyCatalogAgent:
    """Agente responsável por ler e manter o cache do catálogo Hevy."""

    def __init__(self, db: Session, client: HevyClient | None = None) -> None:
        self.db = db
        self.client = client
        self.template_repo = ExerciseTemplateRepository(db)
        self.folder_repo = RoutineFolderRepository(db)
        self.routine_repo = RoutineRepository(db)

    def sync_all(self) -> dict[str, int | list[str]]:
        """Sincroniza templates, pastas e rotinas, isolando falhas por recurso."""
        result: dict[str, int | list[str]] = {
            "templates_synced": 0,
            "folders_synced": 0,
            "routines_synced": 0,
            "errors": [],
        }
        client = self.client or HevyClient()
        resources: tuple[tuple[str, str, Callable[[int], dict[str, Any]], Callable[[dict[str, Any]], None]], ...] = (
            ("Templates", "exercise_templates", client.get_exercise_templates, self._upsert_template),
            ("Folders", "routine_folders", client.get_routine_folders, self._upsert_folder),
            ("Routines", "routines", client.get_routines, self._upsert_routine),
        )

        try:
            for label, collection_key, fetch_page, upsert in resources:
                try:
                    count = self._sync_pages(fetch_page, collection_key, upsert)
                    result[f"{label.lower()}_synced"] = count
                except Exception as exc:
                    self.db.rollback()
                    errors = result["errors"]
                    assert isinstance(errors, list)
                    errors.append(f"{label}: {exc}")
        finally:
            if self.client is None:
                client.close()
        return result

    def _sync_pages(
        self,
        fetch_page: Callable[[int], dict[str, Any]],
        collection_key: str,
        upsert: Callable[[dict[str, Any]], None],
    ) -> int:
        page = 1
        synced = 0
        while True:
            response = fetch_page(page)
            items = response.get(collection_key, [])
            if not isinstance(items, list):
                raise ValueError(f"Campo {collection_key} deve ser uma lista")
            for item in items:
                if not isinstance(item, dict):
                    raise ValueError(f"Item inválido em {collection_key}")
                upsert(item)
                synced += 1
            page_count = response.get("page_count", 1)
            if not isinstance(page_count, int) or page_count < page:
                raise ValueError("page_count inválido na resposta da API Hevy")
            if page >= page_count:
                self.db.commit()
                return synced
            page += 1

    def _upsert_template(self, data: dict[str, Any]) -> None:
        template_id = str(data["id"])
        template = self.template_repo.get_by_id(template_id)
        if template is None:
            template = ExerciseTemplate(id=template_id, title=str(data["title"]))
            self.db.add(template)
        template.title = str(data["title"])
        template.type = data.get("type")
        template.primary_muscle_group = data.get("primary_muscle_group")
        secondary_groups = data.get("secondary_muscle_groups")
        template.secondary_muscle_groups = json.dumps(secondary_groups) if secondary_groups is not None else None
        template.equipment = data.get("equipment")
        template.is_custom = bool(data.get("is_custom", False))

    def _upsert_folder(self, data: dict[str, Any]) -> None:
        folder_id = int(data["id"])
        folder = self.folder_repo.get_by_id(folder_id)
        if folder is None:
            folder = RoutineFolder(id=folder_id, title=str(data["title"]))
            self.db.add(folder)
        folder.title = str(data["title"])
        folder.index = data.get("index")

    def _upsert_routine(self, data: dict[str, Any]) -> None:
        routine_id = str(data["id"])
        routine = self.routine_repo.get_by_id(routine_id)
        if routine is None:
            routine = Routine(id=routine_id, title=str(data["title"]))
            self.db.add(routine)
        routine.title = str(data["title"])
        routine.folder_id = data.get("folder_id")

    def get_template_by_title(self, title: str) -> ExerciseTemplate | None:
        return self.template_repo.get_by_title(title)

    def search_templates(self, query: str) -> list[ExerciseTemplate]:
        statement = select(ExerciseTemplate).where(ExerciseTemplate.title.ilike(f"%{query}%"))
        return list(self.db.scalars(statement.order_by(ExerciseTemplate.title)))

    def get_all_templates(self) -> list[ExerciseTemplate]:
        return self.template_repo.get_all()

    def get_folder_by_id(self, folder_id: int) -> RoutineFolder | None:
        return self.folder_repo.get_by_id(folder_id)

    def get_routine_by_id(self, routine_id: str) -> Routine | None:
        return self.routine_repo.get_by_id(routine_id)
