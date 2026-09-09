from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from src.agents.ai_export_agent import (
    AIExportAgent,
    AIExportError,
    ExportStorageError,
    ImportNotFoundError,
    UnsafeImportIdError,
)
from src.infrastructure.database import get_db

router = APIRouter(prefix="/ai-export", tags=["External AI Export"])


def _download_path(import_id: str, suffix: str) -> Path:
    directory = AIExportAgent._export_directory(import_id)
    path = directory / f"mfit_ai_{suffix}_{import_id}.{'md' if suffix == 'prompt' else 'json'}"
    resolved_directory = directory.resolve()
    resolved_path = path.resolve()
    if resolved_directory not in resolved_path.parents or not resolved_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Pacote não encontrado. Gere o pacote primeiro.",
        )
    return resolved_path


@router.post("/{import_id}")
async def generate_external_ai_package(import_id: str, db: Session = Depends(get_db)):
    try:
        return AIExportAgent(db).export_import_for_external_ai(import_id)
    except ImportNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ExportStorageError as error:
        raise HTTPException(status_code=500, detail="Erro ao armazenar o pacote de exportação.") from error
    except (UnsafeImportIdError, AIExportError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except OSError as error:
        raise HTTPException(status_code=500, detail="Erro ao armazenar o pacote de exportação.") from error


@router.get("/{import_id}/download/prompt")
async def download_external_ai_prompt(import_id: str):
    try:
        path = _download_path(import_id, "prompt")
    except UnsafeImportIdError as error:
        raise HTTPException(status_code=404, detail="Pacote não encontrado. Gere o pacote primeiro.") from error
    return FileResponse(
        path,
        media_type="text/markdown; charset=utf-8",
        filename=path.name,
    )


@router.get("/{import_id}/download/context")
async def download_external_ai_context(import_id: str):
    try:
        path = _download_path(import_id, "context")
    except UnsafeImportIdError as error:
        raise HTTPException(status_code=404, detail="Pacote não encontrado. Gere o pacote primeiro.") from error
    return FileResponse(
        path,
        media_type="application/json",
        filename=path.name,
    )
