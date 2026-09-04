"""
Pytest configuration and fixtures
"""

import os
import tempfile

import pytest


@pytest.fixture
def temp_db():
    """Temporary database for testing"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture
def test_env(temp_db, monkeypatch):
    """Test environment with temporary database"""
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{temp_db}")
    monkeypatch.setenv("ENV", "testing")
    monkeypatch.setenv("HEVY_API_KEY", "test-key-do-not-use")


@pytest.fixture
def client(test_env):
    """FastAPI test client"""
    from fastapi.testclient import TestClient

    from src.api.main import app

    return TestClient(app)


@pytest.fixture
def sample_pdf():
    """Sample PDF for testing parsing"""
    # TODO: Create or mock a sample PDF
    pass
