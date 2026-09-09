from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from src.agents.ai_response_import_agent import (
    AIResponseImportAgent,
    AIResponseImportError,
    ResponseImportMismatchError,
    ResponseImportNotFoundError,
    ResponsePayloadError,
    ResponseSchemaError,
)
from src.infrastructure.database import get_db

router = APIRouter(prefix="/ai-response", tags=["External AI Response"])
MAX_UPLOAD_BYTES = 5 * 1024 * 1024


@router.post("/import")
async def import_external_ai_response(file: UploadFile = File(...), db: Session = Depends(get_db)):
    filename = file.filename or ""
    content_type = (file.content_type or "").lower()
    if not filename.lower().endswith(".json") or content_type != "application/json":
        raise HTTPException(status_code=400, detail="Envie um arquivo .json com MIME application/json.")
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="O arquivo JSON excede o limite de 5 MB.")
    try:
        result = AIResponseImportAgent(db).import_external_ai_response(content, filename)
    except ResponseImportNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ResponseImportMismatchError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except ResponseSchemaError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except ResponsePayloadError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except AIResponseImportError as error:
        raise HTTPException(status_code=500, detail="Não foi possível importar a resposta da IA.") from error
    if result.get("status") == "rejected":
        raise HTTPException(status_code=409, detail=result)
    return result


@router.get("/{import_id}/validation-report")
def get_external_ai_validation_report(import_id: str, db: Session = Depends(get_db)):
    try:
        report = AIResponseImportAgent(db).get_latest_validation_report(import_id)
    except ResponseImportNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    if report is None:
        raise HTTPException(status_code=404, detail="Nenhum relatório de validação está disponível.")
    return report
