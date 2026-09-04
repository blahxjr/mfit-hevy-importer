"""Agente que extrai um PDF MFIT e persiste seu estado bruto."""
import hashlib
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from src.domain.models import Import, SourceExercise, SourceWorkout
from src.parsers.mfit_parser import MFITParser
from src.repositories.import_repository import ImportRepository


class MFITParserAgent:
    def __init__(self, db: Session):
        self.db, self.import_repo = db, ImportRepository(db)

    def parse_and_save(self, pdf_path: str) -> dict[str, Any]:
        file_hash = hashlib.sha256(Path(pdf_path).read_bytes()).hexdigest()
        existing = self.import_repo.get_by_sha256(file_hash)
        if existing:
            return {
                "import_id": existing.id,
                "filename": existing.filename,
                "sha256": file_hash,
                "status": "duplicate",
                "message": "File already imported",
            }
        parsed = MFITParser(pdf_path).parse()
        imported = Import(id=str(uuid.uuid4()), filename=parsed.filename, sha256=file_hash, status="parsed")
        self.db.add(imported)
        workouts_count = exercises_count = 0
        for workout in parsed.workouts:
            persisted = SourceWorkout(import_ref=imported, source_name=workout.source_name, order=workout.order)
            self.db.add(persisted)
            workouts_count += 1
            for exercise in workout.exercises:
                self.db.add(
                    SourceExercise(
                        workout_ref=persisted,
                        source_name=exercise.source_name,
                        order=exercise.order,
                        sets_raw=exercise.sets_raw,
                        reps_raw=exercise.reps_raw,
                        load_raw=exercise.load_raw,
                        rest_raw=exercise.rest_raw,
                        notes_raw=exercise.notes_raw,
                        techniques=",".join(exercise.techniques) or None,
                        group_id=exercise.group_id,
                        source_location=exercise.source_location,
                        confidence=exercise.confidence,
                    )
                )
                exercises_count += 1
        self.db.commit()
        return {
            "import_id": imported.id,
            "filename": parsed.filename,
            "sha256": file_hash,
            "status": "parsed",
            "workouts_count": workouts_count,
            "exercises_count": exercises_count,
            "warnings": parsed.warnings,
        }
