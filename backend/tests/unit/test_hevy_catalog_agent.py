import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.agents.hevy_catalog_agent import HevyCatalogAgent
from src.domain.models import Base, ExerciseTemplate, Routine, RoutineFolder
from src.hevy.client import HevyClient


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    engine.dispose()


class FakeHevyClient:
    def get_exercise_templates(self, page: int):
        responses = {
            1: {
                "page": 1,
                "page_count": 2,
                "exercise_templates": [
                    {
                        "id": "first",
                        "title": "Supino Reto",
                        "type": "strength",
                        "primary_muscle_group": "chest",
                        "secondary_muscle_groups": ["triceps"],
                        "equipment": "barbell",
                        "is_custom": False,
                    }
                ],
            },
            2: {
                "page": 2,
                "page_count": 2,
                "exercise_templates": [
                    {
                        "id": "second",
                        "title": "Supino Inclinado",
                        "type": "strength",
                        "primary_muscle_group": "chest",
                        "secondary_muscle_groups": [],
                        "equipment": "dumbbell",
                        "is_custom": True,
                    }
                ],
            },
        }
        return responses[page]

    def get_routine_folders(self, page: int):
        return {"page": 1, "page_count": 1, "routine_folders": [{"id": 1, "title": "Força", "index": 0}]}

    def get_routines(self, page: int):
        return {"page": 1, "page_count": 1, "routines": [{"id": "routine-1", "title": "Treino A", "folder_id": 1}]}


def test_client_uses_api_key_and_retries_rate_limit():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(429, headers={"Retry-After": "0"}, request=request)
        return httpx.Response(200, json={"page": 1, "page_count": 1, "exercise_templates": []}, request=request)

    client = HevyClient(api_key="test-key", transport=httpx.MockTransport(handler), sleep=lambda _: None)
    assert client.get_exercise_templates() == {"page": 1, "page_count": 1, "exercise_templates": []}
    assert len(calls) == 2
    assert calls[0].headers["api-key"] == "test-key"
    assert calls[0].url.params["page"] == "1"
    client.close()


def test_sync_all_paginates_persists_and_is_idempotent(db_session):
    agent = HevyCatalogAgent(db_session, client=FakeHevyClient())

    first_result = agent.sync_all()
    second_result = agent.sync_all()

    assert first_result == {"templates_synced": 2, "folders_synced": 1, "routines_synced": 1, "errors": []}
    assert second_result == first_result
    assert db_session.query(ExerciseTemplate).count() == 2
    assert db_session.query(RoutineFolder).count() == 1
    assert db_session.query(Routine).count() == 1
    assert agent.search_templates("inclinado")[0].id == "second"


def test_sync_all_records_resource_error_and_continues(db_session):
    class FailingTemplateClient(FakeHevyClient):
        def get_exercise_templates(self, page: int):
            raise httpx.ConnectError("offline")

    result = HevyCatalogAgent(db_session, client=FailingTemplateClient()).sync_all()

    assert result["templates_synced"] == 0
    assert result["folders_synced"] == 1
    assert result["routines_synced"] == 1
    assert result["errors"] == ["Templates: offline"]
