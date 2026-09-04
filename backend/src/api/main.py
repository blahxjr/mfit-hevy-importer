"""
Main FastAPI application
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes.catalog import router as catalog_router
from src.api.routes.imports import router as imports_router
from src.api.routes.mapping import router as mapping_router
from src.api.routes.normalize import router as normalize_router
from src.api.routes.review import router as review_router
from src.api.routes.write import router as write_router
from src.infrastructure.config import settings
from src.schemas.core import ImportState, ImportStatus


# Lifespan event
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown"""
    print("🚀 Starting MFIT → Hevy Orchestrator")
    # TODO: Initialize database, connect to cache, etc.
    yield
    print("🛑 Shutting down MFIT → Hevy Orchestrator")
    # TODO: Close connections


# Create app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.env == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(catalog_router)
app.include_router(imports_router)
app.include_router(normalize_router)
app.include_router(mapping_router)
app.include_router(review_router)
app.include_router(write_router)


# Health check
@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": settings.api_version,
        "environment": settings.env,
    }


# Import endpoints (placeholder)
@app.post("/imports/upload", tags=["Imports"])
async def upload_workout(file: UploadFile = File(...)):
    """Upload a workout file (PDF or image)"""
    # TODO: Implement upload logic
    return {
        "message": "Upload endpoint - to be implemented",
        "filename": file.filename,
    }


@app.get("/imports/{import_id}", tags=["Imports"])
async def get_import_state(import_id: str):
    """Get the current state of an import"""
    # TODO: Implement state retrieval
    return {
        "message": "Get import state endpoint - to be implemented",
        "import_id": import_id,
    }


@app.post("/imports/{import_id}/approve", tags=["Imports"])
async def approve_import(import_id: str, corrections: dict = None):
    """Approve an import after review"""
    # TODO: Implement approval logic
    return {
        "message": "Approve import endpoint - to be implemented",
        "import_id": import_id,
    }


# API version
@app.get("/", tags=["Info"])
async def root():
    """API information"""
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "description": settings.api_description,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
