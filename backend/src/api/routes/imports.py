import os
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.agents.mfit_parser_agent import MFITParserAgent
from src.domain.models import ExerciseMapping, SourceExercise, SourceWorkout
from src.infrastructure.database import get_db
from src.repositories.import_repository import ImportRepository
from src.repositories.workout_exercise_media_repository import WorkoutExerciseMediaRepository
from src.services.generic_movement_library_service import GenericMovementLibraryService
from src.services.workout_exercise_visual_service import WorkoutExerciseVisualService

router = APIRouter(prefix="/imports", tags=["Imports"])


@router.post("/parse")
async def parse_mfit_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temporary:
        temporary.write(await file.read())
        path = temporary.name
    try:
        return MFITParserAgent(db).parse_and_save(path)
    finally:
        os.unlink(path)


def _imports_root() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "imports"


def _valid_import_id(import_id: str) -> str:
    try:
        return str(uuid.UUID(import_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Import not found") from exc


@router.get("/{import_id}/pdf")
def get_original_pdf(import_id: str, db: Session = Depends(get_db)) -> FileResponse:
    safe_id = _valid_import_id(import_id)
    if ImportRepository(db).get_by_id(safe_id) is None:
        raise HTTPException(status_code=404, detail="Import not found")
    pdf_path = _imports_root() / safe_id / "original.pdf"
    if not pdf_path.is_file() or pdf_path.parent.parent != _imports_root():
        raise HTTPException(status_code=404, detail="Original PDF not found")
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=original.pdf"},
    )


def _exercise_context(db: Session, import_id: str, exercise_index: int):
    if exercise_index < 0:
        raise HTTPException(status_code=400, detail="exercise_index inválido")
    workouts = db.scalars(
        select(SourceWorkout)
        .options(selectinload(SourceWorkout.exercises))
        .where(SourceWorkout.import_id == import_id)
        .order_by(SourceWorkout.order)
    ).all()
    flattened = [exercise for workout in workouts for exercise in sorted(workout.exercises, key=lambda item: item.order)]
    if exercise_index >= len(flattened):
        raise HTTPException(status_code=404, detail="Exercise not found")
    exercise = flattened[exercise_index]
    mapping = db.scalar(select(ExerciseMapping).where(ExerciseMapping.source_name == exercise.source_name))
    template = mapping.template if mapping and mapping.template else None
    return exercise, template


def _visual(db: Session, import_id: str, exercise_index: int) -> dict[str, object]:
    exercise, template = _exercise_context(db, import_id, exercise_index)
    media = WorkoutExerciseMediaRepository(db).get_by_import_and_index(import_id, exercise_index)
    generic = GenericMovementLibraryService.get_generic_media_for_template(template)
    return WorkoutExerciseVisualService.get_visual_descriptor_for_workout_exercise(
        import_id, exercise_index, template, media, generic
    ) | {"exercise_name": exercise.source_name}


@router.get("/{import_id}/exercises/{exercise_index}/media")
def get_workout_exercise_media(import_id: str, exercise_index: int, db: Session = Depends(get_db)):
    safe_id = _valid_import_id(import_id)
    if ImportRepository(db).get_by_id(safe_id) is None:
        raise HTTPException(status_code=404, detail="Import not found")
    return _visual(db, safe_id, exercise_index)


@router.post("/{import_id}/exercises/{exercise_index}/media/upload")
async def upload_workout_exercise_media(
    import_id: str,
    exercise_index: int,
    file: UploadFile = File(...),
    alt_text: str = Form(...),
    source: str = Form("local_manual"),
    is_verified: bool = Form(False),
    db: Session = Depends(get_db),
):
    safe_id = _valid_import_id(import_id)
    if ImportRepository(db).get_by_id(safe_id) is None:
        raise HTTPException(status_code=404, detail="Import not found")
    _, template = _exercise_context(db, safe_id, exercise_index)
    if source != "local_manual":
        raise HTTPException(status_code=400, detail="source permitido apenas local_manual")
    if not alt_text.strip() or len(alt_text) > 255:
        raise HTTPException(status_code=400, detail="alt_text obrigatório e limitado a 255 caracteres")
    if is_verified and not str(is_verified).lower() in {"true", "1", "on"}:
        raise HTTPException(status_code=400, detail="Confirmação de verificação inválida")
    content_type = (file.content_type or "").lower()
    allowed = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}
    suffix = Path(file.filename or "").suffix.lower()
    if content_type not in allowed or suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise HTTPException(status_code=400, detail="Formato de imagem não permitido")
    contents = await file.read()
    if len(contents) > 3 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Imagem excede 3 MB")
    valid_png = contents[:8] == b"\x89PNG\r\n\x1a\n"
    valid_jpeg = contents[:2] == b"\xff\xd8"
    valid_webp = contents[:4] == b"RIFF" and contents[8:12] == b"WEBP"
    if not ((content_type == "image/png" and valid_png) or (content_type == "image/jpeg" and valid_jpeg) or (content_type == "image/webp" and valid_webp)):
        raise HTTPException(status_code=400, detail="MIME falso ou arquivo inválido")
    media_dir = _imports_root() / safe_id / "exercise-media" / str(exercise_index)
    media_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"reference_{uuid.uuid4().hex}{allowed[content_type]}"
    (media_dir / file_name).write_bytes(contents)
    WorkoutExerciseMediaRepository(db).upsert_verified_media(
        import_id=safe_id,
        exercise_index=exercise_index,
        template_id=template.id if template else None,
        source="local_manual",
        image_url=f"/static/imports/{safe_id}/exercise-media/{exercise_index}/{file_name}",
        local_file_name=file_name,
        alt_text=alt_text.strip(),
        is_verified=is_verified,
    )
    return _visual(db, safe_id, exercise_index)


@router.put("/{import_id}/exercises/{exercise_index}/media")
def update_workout_exercise_media(
    import_id: str,
    exercise_index: int,
    payload: dict[str, object] = Body(...),
    db: Session = Depends(get_db),
):
    safe_id = _valid_import_id(import_id)
    media = WorkoutExerciseMediaRepository(db).get_by_import_and_index(safe_id, exercise_index)
    if media is None or media.source != "local_manual":
        raise HTTPException(status_code=404, detail="Local media not found")
    alt_text = payload.get("alt_text")
    if not isinstance(alt_text, str) or not alt_text.strip() or len(alt_text) > 255:
        raise HTTPException(status_code=400, detail="alt_text obrigatório e limitado a 255 caracteres")
    if not isinstance(payload.get("is_verified"), bool):
        raise HTTPException(status_code=400, detail="is_verified deve ser booleano")
    media.alt_text = alt_text.strip()
    media.is_verified = payload["is_verified"]
    db.commit()
    return _visual(db, safe_id, exercise_index)


@router.get("/generic_movement_library")
def get_generic_movement_library() -> dict[str, object]:
    import json
    mapping_path = Path(__file__).resolve().parents[3] / "data" / "generic-movement-library" / "mapping.json"
    return json.loads(mapping_path.read_text(encoding="utf-8")) if mapping_path.exists() else {"movements": {}, "template_to_movement": {}}
