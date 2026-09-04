"""Configuração de engine e sessões SQLAlchemy síncronas."""

from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.domain.models import Base
from src.infrastructure.config import settings


def create_database_engine(database_url: str | None = None) -> Engine:
    """Cria uma engine compatível com SQLite local e PostgreSQL em produção."""
    url = database_url or settings.database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, echo=False, connect_args=connect_args)


engine = create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Cria tabelas quando a aplicação é usada sem migrations."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Fornece uma sessão por requisição FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
