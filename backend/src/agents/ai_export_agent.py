"""Exporta contexto MFIT e prompt para uso manual com IA externa."""

import hashlib
import json
import os
import re
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.models import AuditEvent, Import, SourceExercise, SourceWorkout

IMPORT_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
PLACEHOLDER = "{{MFIT_AI_CONTEXT_JSON}}"


class AIExportError(Exception):
    """Erro controlado durante a geração do pacote externo."""


class ImportNotFoundError(AIExportError):
    """A importação local solicitada não existe."""


class UnsafeImportIdError(AIExportError):
    """O identificador não pode ser usado em um caminho de arquivo."""


class ExportStorageError(AIExportError):
    """Não foi possível ler ou gravar o pacote local."""


class AIExportAgent:
    """Gera exclusivamente artefatos locais para canonicalização manual."""

    def __init__(self, db: Session):
        self.db = db

    def export_import_for_external_ai(self, import_id: str) -> dict:
        self._validate_import_id(import_id)
        imported = self.db.scalar(select(Import).where(Import.id == import_id))
        if imported is None:
            raise ImportNotFoundError(f"Importação não encontrada: {import_id}")

        workouts = list(
            self.db.scalars(
                select(SourceWorkout).where(SourceWorkout.import_id == import_id).order_by(SourceWorkout.order)
            )
        )
        context = {
            "schema_version": "1.0",
            "import_id": import_id,
            "source_filename": self._sanitize_text(imported.filename),
            "workouts": [],
        }
        exercises_count = 0
        for workout in workouts:
            exercises = list(
                self.db.scalars(
                    select(SourceExercise).where(SourceExercise.workout_id == workout.id).order_by(SourceExercise.order)
                )
            )
            exported_exercises = [self._export_exercise(exercise) for exercise in exercises]
            exercises_count += len(exported_exercises)
            context["workouts"].append(
                {
                    "source_workout_order": workout.order,
                    "source_workout_name_pt": self._sanitize_text(workout.source_name),
                    "exercises": exported_exercises,
                }
            )

        context_json = self._serialize_json(context)
        prompt_template = self._load_prompt_template()
        prompt = prompt_template.replace(PLACEHOLDER, context_json)
        prompt_bytes = prompt.encode("utf-8")
        context_bytes = context_json.encode("utf-8")

        export_directory = self._export_directory(import_id)
        prompt_path = export_directory / f"mfit_ai_prompt_{import_id}.md"
        context_path = export_directory / f"mfit_ai_context_{import_id}.json"
        regenerated = prompt_path.is_file() and context_path.is_file()
        try:
            export_directory.mkdir(parents=True, exist_ok=True)
            prompt_path.write_bytes(prompt_bytes)
            context_path.write_bytes(context_bytes)
            self._record_audit(
                imported.id,
                prompt_path.name,
                context_path.name,
                len(workouts),
                exercises_count,
                hashlib.sha256(context_bytes).hexdigest(),
                hashlib.sha256(prompt_bytes + context_bytes).hexdigest(),
            )
        except OSError as error:
            raise ExportStorageError("Não foi possível armazenar o pacote de exportação.") from error

        return {
            "import_id": import_id,
            "status": "exported",
            "regenerated": regenerated,
            "prompt_filename": prompt_path.name,
            "context_filename": context_path.name,
            "prompt_relative_path": self._relative_export_path(prompt_path),
            "context_relative_path": self._relative_export_path(context_path),
            "workouts_count": len(workouts),
            "exercises_count": exercises_count,
        }

    @classmethod
    def export_root(cls) -> Path:
        configured = os.getenv("AI_EXPORT_ROOT")
        if configured:
            return Path(configured).expanduser().resolve()
        return Path(__file__).resolve().parents[2] / "data" / "exports"

    @classmethod
    def _export_directory(cls, import_id: str) -> Path:
        cls._validate_import_id(import_id)
        return cls.export_root() / import_id

    @classmethod
    def _relative_export_path(cls, path: Path) -> str:
        return path.relative_to(cls.export_root()).as_posix()

    @staticmethod
    def _validate_import_id(import_id: str) -> None:
        if not isinstance(import_id, str) or not IMPORT_ID_PATTERN.fullmatch(import_id) or ".." in import_id:
            raise UnsafeImportIdError("import_id inválido para exportação local.")

    @staticmethod
    def _sanitize_text(value: str | None) -> str | None:
        if value is None:
            return None
        sanitized = re.sub(
            r"(?i)(api[_ -]?key|token|password|secret)\s*[:=]\s*[^\s,;]+",
            r"\1=[REDACTED]",
            value,
        )
        sanitized = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", sanitized)
        return sanitized

    @classmethod
    def _export_exercise(cls, exercise: SourceExercise) -> dict:
        return {
            "source_exercise_id": exercise.id,
            "source_exercise_order": exercise.order,
            "source_name_pt": cls._sanitize_text(exercise.source_name),
            "sets_raw": cls._sanitize_text(exercise.sets_raw),
            "reps_raw": cls._sanitize_text(exercise.reps_raw),
            "load_raw": cls._sanitize_text(exercise.load_raw),
            "rest_raw": cls._sanitize_text(exercise.rest_raw),
            "notes_raw": cls._sanitize_text(exercise.notes_raw),
            "techniques": cls._techniques_as_list(exercise.techniques),
            "group_id": exercise.group_id,
        }

    @staticmethod
    def _techniques_as_list(value: str | None) -> list[str]:
        if not value:
            return []
        try:
            decoded = json.loads(value)
        except (TypeError, json.JSONDecodeError):
            decoded = None
        if isinstance(decoded, list):
            return [str(item).strip() for item in decoded if str(item).strip()]
        if isinstance(decoded, str):
            value = decoded
        return [item.strip() for item in re.split(r"[,;\n]", value) if item.strip()]

    @staticmethod
    def _serialize_json(context: dict) -> str:
        return json.dumps(context, ensure_ascii=False, indent=2) + "\n"

    @staticmethod
    def _load_prompt_template() -> str:
        template_path = Path(__file__).resolve().parents[3] / "docs" / "prompts" / "exercise-canonicalization-v1.md"
        try:
            template = template_path.read_text(encoding="utf-8")
        except OSError as error:
            raise ExportStorageError("Template do prompt não está disponível.") from error
        if PLACEHOLDER not in template:
            raise ExportStorageError("Template do prompt não contém o placeholder esperado.")
        return template

    def _record_audit(
        self,
        import_id: str,
        prompt_filename: str,
        context_filename: str,
        workouts_count: int,
        exercises_count: int,
        input_hash: str,
        output_hash: str,
    ) -> None:
        audit = AuditEvent(
            import_id=import_id,
            agent_name="AIExportAgent",
            agent_version="1.0",
            input_hash=input_hash,
            output_hash=output_hash,
            warnings=json.dumps(
                {
                    "prompt_filename": prompt_filename,
                    "context_filename": context_filename,
                    "workouts_count": workouts_count,
                    "exercises_count": exercises_count,
                },
                ensure_ascii=False,
            ),
        )
        self.db.add(audit)
        self.db.commit()
