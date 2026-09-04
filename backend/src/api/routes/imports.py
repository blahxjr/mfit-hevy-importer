import os
import tempfile

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from src.agents.mfit_parser_agent import MFITParserAgent
from src.infrastructure.database import get_db

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
