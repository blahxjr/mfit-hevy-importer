"""Endpoints de consulta e sincronização do catálogo Hevy."""

from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from src.agents.hevy_catalog_agent import HevyCatalogAgent
from src.domain.models import ExerciseTemplate
from src.infrastructure.database import get_db
from src.repositories.exercise_template_media_repository import ExerciseTemplateMediaRepository
from src.services.exercise_visual_service import ExerciseVisualService

router = APIRouter(prefix="/catalog", tags=["Catalog"])


@router.post("/sync")
def sync_catalog(db: Session = Depends(get_db)) -> dict[str, int | list[str]]:
    """Sincroniza o cache do catálogo usando a API Hevy."""
    result = HevyCatalogAgent(db).sync_all()
    if result["errors"]:
        raise HTTPException(status_code=502, detail=result)
    return result


@router.get("/templates")
def list_templates(db: Session = Depends(get_db)) -> dict[str, list[dict[str, str | None]]]:
    """Lista templates disponíveis no cache local."""
    templates = HevyCatalogAgent(db).get_all_templates()
    return {"templates": [{"id": item.id, "title": item.title, "type": item.type} for item in templates]}


@router.get("/templates/search")
def search_templates(
    q: str = Query(min_length=1), limit: int = Query(default=20, ge=1, le=100), db: Session = Depends(get_db)
) -> dict[str, object]:
    """Busca templates no cache local, sem chamar a API Hevy."""
    templates = HevyCatalogAgent(db).search_templates(q, limit)
    return {
        "templates": [
            {
                "id": item.id,
                "title": item.title,
                "type": item.type,
                "primary_muscle_group": item.primary_muscle_group,
                "equipment": item.equipment,
                "is_custom": item.is_custom,
            }
            for item in templates
        ],
        "query": q,
        "count": len(templates),
    }


@router.get("/templates/{template_id}/media")
def get_template_media(template_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    """Retorna o descritor visual seguro do template, inclusive placeholder local."""
    template = db.get(ExerciseTemplate, template_id)
    media = ExerciseTemplateMediaRepository(db).get_by_template_id(template_id)
    return ExerciseVisualService.get_visual_descriptor(template, media)


@router.post("/templates/{template_id}/media/upload")
async def upload_template_media(
    template_id: str,
    file: UploadFile = File(...),
    alt_text: str = Form(...),
    source: str = Form("local_manual"),
    is_verified: bool = Form(False),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Aceita upload local de imagem como referência visual apenas, sem alterar o mapeamento."""
    if source != "local_manual":
        raise HTTPException(status_code=400, detail="source permitido apenas local_manual")
    template = db.get(ExerciseTemplate, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    if file.filename is None or not file.filename.strip():
        raise HTTPException(status_code=400, detail="Nome de arquivo obrigatório")
    if (file.content_type or "").lower() not in {"image/png", "image/jpeg", "image/webp"}:
        raise HTTPException(status_code=400, detail="Formato de imagem não permitido")
    allowed_exts = {".png", ".jpg", ".jpeg", ".webp"}
    suffix = Path(file.filename).suffix.lower()
    if suffix not in allowed_exts:
        raise HTTPException(status_code=400, detail="Extensão de arquivo inválida")
    contents = await file.read()
    if len(contents) > 3 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Imagem excede 3 MB")

    signature = contents[:8]
    valid_png = signature.startswith(b"\x89PNG\r\n\x1a\n")
    valid_jpeg = signature[:2] == b"\xff\xd8"
    valid_webp = signature[:4] == b"RIFF" and signature[8:12] == b"WEBP"
    if not (valid_png or valid_jpeg or valid_webp):
        raise HTTPException(status_code=400, detail="MIME falso ou arquivo inválido")
    if ".." in file.filename or "/" in file.filename or "\\" in file.filename:
        raise HTTPException(status_code=400, detail="Nome de arquivo inváldo")

    media_dir = Path("./data/template-media") / template_id
    media_dir.mkdir(parents=True, exist_ok=True)
    file_stem = f"{template_id}_{uuid.uuid4().hex}{suffix}"
    destination = media_dir / file_stem
    destination.write_bytes(contents)

    repo = ExerciseTemplateMediaRepository(db)
    media = repo.upsert_verified_media(
        template_id=template_id,
        source=source,
        image_url=f"/template-media/{template_id}/{file_stem}",
        local_file_name=file_stem,
        alt_text=alt_text,
        attribution=None,
        is_verified=is_verified,
    )
    return ExerciseVisualService.get_visual_descriptor(template, media)
