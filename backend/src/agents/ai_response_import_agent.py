"""Valida e persiste respostas externas de canonicalização sem alterar a ficha MFIT."""

import hashlib
import json
from typing import Any

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.domain.models import AuditEvent, Import, SourceExercise, SourceWorkout
from src.repositories.exercise_canonicalization_repository import ExerciseCanonicalizationRepository
from src.schemas.external_ai_response import ExternalAIResponse

MAX_RESPONSE_BYTES = 5 * 1024 * 1024
MAX_SANITIZED_RESPONSE_BYTES = 512 * 1024


class AIResponseImportError(Exception):
    """Erro controlado na importação da resposta externa."""


class ResponsePayloadError(AIResponseImportError):
    """JSON vazio, inválido ou incompatível com o schema."""


class ResponseSchemaError(ResponsePayloadError):
    """JSON válido, mas incompatível com o schema Pydantic."""


class ResponseImportNotFoundError(AIResponseImportError):
    """Import local não encontrado."""


class ResponseImportMismatchError(AIResponseImportError):
    """Resposta válida, mas inconsistente com o import local."""


class AIResponseImportAgent:
    def __init__(self, db: Session):
        self.db = db
        self.repository = ExerciseCanonicalizationRepository(db)

    def import_external_ai_response(self, file_content: bytes, original_filename: str | None = None) -> dict:
        if not file_content:
            raise ResponsePayloadError("O arquivo JSON está vazio.")
        if len(file_content) > MAX_RESPONSE_BYTES:
            raise ResponsePayloadError("O arquivo JSON excede o limite de 5 MB.")
        try:
            payload_text = file_content.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ResponsePayloadError("O arquivo não está codificado em UTF-8.") from error
        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError as error:
            raise ResponsePayloadError(f"JSON inválido na linha {error.lineno}, coluna {error.colno}.") from error
        try:
            response = ExternalAIResponse.model_validate(payload)
        except ValidationError as error:
            raise ResponseSchemaError(self._validation_error_message(error)) from error

        imported = self.db.scalar(select(Import).where(Import.id == response.import_id))
        if imported is None:
            raise ResponseImportNotFoundError("O import_id informado não existe localmente.")
        if response.source_filename != imported.filename:
            raise ResponseImportMismatchError(
                "source_filename diverge do arquivo original desta importação; a resposta foi bloqueada."
            )

        workouts = list(
            self.db.scalars(
                select(SourceWorkout).where(SourceWorkout.import_id == imported.id).order_by(SourceWorkout.order)
            )
        )
        local_exercises: dict[int, list[SourceExercise]] = {}
        for workout in workouts:
            local_exercises[workout.id] = list(
                self.db.scalars(
                    select(SourceExercise).where(SourceExercise.workout_id == workout.id).order_by(SourceExercise.order)
                )
            )

        errors = self._validate_structure(response, workouts, local_exercises)
        validation_report = self._validation_report(response, workouts, local_exercises, errors)
        if errors:
            result = {
                "import_id": response.import_id,
                "status": "rejected",
                "provider": response.generated_by.provider.value,
                "model_name": response.generated_by.model,
                "accepted_count": 0,
                "created_count": 0,
                "updated_count": 0,
                "rejected_count": validation_report["exercises_received"],
                "warnings": [
                    "Nenhuma canonicalização foi persistida porque a resposta não corresponde ao import local."
                ],
                "validation_report": validation_report,
            }
            self._record_audit(imported.id, result, file_content)
            return result

        sanitized = self._sanitized_response(response)
        created_count = 0
        updated_count = 0
        try:
            for workout in workouts:
                local_by_id = {exercise.id: exercise for exercise in local_exercises[workout.id]}
                incoming_workout = next(
                    item for item in response.workouts if item.source_workout_order == workout.order
                )
                for incoming in incoming_workout.exercises:
                    existing = self.repository.get_by_source_exercise_id(incoming.source_exercise_id)
                    if existing is None:
                        created_count += 1
                    else:
                        updated_count += 1
                    self.repository.upsert(
                        source_exercise_id=incoming.source_exercise_id,
                        source_name_pt=local_by_id[incoming.source_exercise_id].source_name,
                        canonical_name_en=incoming.canonical_name_en,
                        search_aliases_en=incoming.search_aliases_en,
                        movement_pattern=incoming.movement_pattern.value if incoming.movement_pattern else None,
                        equipment_hint=incoming.equipment_hint.value if incoming.equipment_hint else None,
                        primary_muscle_hint=incoming.primary_muscle_hint,
                        secondary_muscles_hint=incoming.secondary_muscles_hint,
                        confidence=incoming.confidence,
                        needs_review=True,
                        review_reason=incoming.review_reason,
                        provider=response.generated_by.provider.value,
                        model_name=response.generated_by.model,
                        prompt_version="v1",
                        raw_response_sanitized=sanitized,
                        commit=False,
                    )
            result = {
                "import_id": response.import_id,
                "status": "imported",
                "provider": response.generated_by.provider.value,
                "model_name": response.generated_by.model,
                "accepted_count": validation_report["exercises_expected"],
                "created_count": created_count,
                "updated_count": updated_count,
                "rejected_count": 0,
                "warnings": [],
                "validation_report": validation_report,
            }
            self.db.commit()
            self._record_audit(imported.id, result, file_content)
            return result
        except SQLAlchemyError as error:
            self.db.rollback()
            raise AIResponseImportError("Não foi possível persistir as canonicalizações.") from error

    def get_latest_validation_report(self, import_id: str) -> dict | None:
        imported = self.db.scalar(select(Import).where(Import.id == import_id))
        if imported is None:
            raise ResponseImportNotFoundError("O import_id informado não existe localmente.")
        event = self.db.scalar(
            select(AuditEvent)
            .where(AuditEvent.import_id == import_id, AuditEvent.agent_name == "AIResponseImportAgent")
            .order_by(AuditEvent.id.desc())
        )
        if event is None or not event.warnings:
            return None
        try:
            report = json.loads(event.warnings)
        except json.JSONDecodeError:
            return None
        return report if isinstance(report, dict) else None

    @staticmethod
    def _validate_structure(response, workouts, local_exercises) -> list[str]:
        errors: list[str] = []
        local_by_order = {workout.order: workout for workout in workouts}
        received_orders = [workout.source_workout_order for workout in response.workouts]
        if len(received_orders) != len(set(received_orders)):
            errors.append("Há treinos duplicados na resposta.")
        if set(received_orders) != set(local_by_order):
            errors.append("A resposta não contém exatamente os treinos locais.")
        for incoming_workout in response.workouts:
            local_workout = local_by_order.get(incoming_workout.source_workout_order)
            if local_workout is None:
                continue
            if incoming_workout.source_workout_name_pt != local_workout.source_name:
                errors.append(f"Nome divergente no treino de ordem {local_workout.order}.")
            local_items = local_exercises[local_workout.id]
            local_by_id = {exercise.id: exercise for exercise in local_items}
            received_ids = [exercise.source_exercise_id for exercise in incoming_workout.exercises]
            if len(received_ids) != len(set(received_ids)):
                errors.append(f"Há exercícios duplicados no treino {local_workout.order}.")
            if set(received_ids) != set(local_by_id):
                errors.append(f"Os exercícios do treino {local_workout.order} não correspondem à ficha local.")
            for incoming_exercise in incoming_workout.exercises:
                local_exercise = local_by_id.get(incoming_exercise.source_exercise_id)
                if local_exercise is None:
                    continue
                if incoming_exercise.source_exercise_order != local_exercise.order:
                    errors.append(f"Ordem divergente no exercício {local_exercise.id}.")
                if incoming_exercise.source_name_pt != local_exercise.source_name:
                    errors.append(f"Nome divergente no exercício {local_exercise.id}.")
        return errors

    @staticmethod
    def _validation_report(response, workouts, local_exercises, errors) -> dict:
        return {
            "valid": not errors,
            "errors": errors,
            "workouts_expected": len(workouts),
            "workouts_received": len(response.workouts),
            "exercises_expected": sum(len(items) for items in local_exercises.values()),
            "exercises_received": sum(len(workout.exercises) for workout in response.workouts),
        }

    @staticmethod
    def _sanitized_response(response: ExternalAIResponse) -> str:
        value: dict[str, Any] = response.model_dump(mode="json")
        for workout in value["workouts"]:
            for exercise in workout["exercises"]:
                exercise.pop("notes_for_hevy_search", None)
        serialized = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        if len(serialized.encode("utf-8")) > MAX_SANITIZED_RESPONSE_BYTES:
            raise ResponsePayloadError("A resposta sanitizada excede o limite seguro de armazenamento.")
        return serialized

    @staticmethod
    def _validation_error_message(error: ValidationError) -> str:
        messages = [f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}" for item in error.errors()]
        return "Resposta incompatível com o schema: " + "; ".join(messages[:10])

    def _record_audit(self, import_id: str, result: dict, file_content: bytes) -> None:
        report = {
            "import_id": result["import_id"],
            "status": result["status"],
            "provider": result["provider"],
            "model_name": result["model_name"],
            "accepted_count": result["accepted_count"],
            "created_count": result["created_count"],
            "updated_count": result["updated_count"],
            "rejected_count": result["rejected_count"],
            "warnings": result["warnings"],
            "validation_report": result["validation_report"],
        }
        self.db.add(
            AuditEvent(
                import_id=import_id,
                agent_name="AIResponseImportAgent",
                agent_version="1.0",
                input_hash=hashlib.sha256(file_content).hexdigest(),
                output_hash=hashlib.sha256(json.dumps(report, sort_keys=True).encode()).hexdigest(),
                warnings=json.dumps(report, ensure_ascii=False),
            )
        )
        self.db.commit()
