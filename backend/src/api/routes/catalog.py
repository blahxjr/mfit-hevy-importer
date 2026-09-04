"""Endpoints de consulta e sincronização do catálogo Hevy."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.agents.hevy_catalog_agent import HevyCatalogAgent
from src.infrastructure.database import get_db

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
def search_templates(q: str = Query(min_length=1), db: Session = Depends(get_db)) -> dict[str, list[dict[str, str]]]:
    """Busca templates no cache por título parcial, sem distinção de maiúsculas."""
    templates = HevyCatalogAgent(db).search_templates(q)
    return {"templates": [{"id": item.id, "title": item.title} for item in templates]}
