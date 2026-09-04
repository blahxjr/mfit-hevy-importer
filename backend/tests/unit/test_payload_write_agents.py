import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.agents.hevy_write_agent import HevyWriteAgent
from src.agents.payload_builder_agent import PayloadBuilderAgent
from src.agents.qa_agent import QAAgent
from src.domain.models import (
    Base,
    ExerciseMapping,
    ExerciseTemplate,
    Import,
    NormalizedExercise,
    SourceExercise,
    SourceWorkout,
)
from src.hevy.client import HevyClient


def make_db(approved=True, confirmed=True):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    template = ExerciseTemplate(id="template-1", title="Lat Pulldown")
    imported = Import(id="import-1", filename="ficha.pdf", sha256="a" * 64, status="approved" if approved else "mapped")
    workout = SourceWorkout(
        import_ref=imported, source_name="A - Costas", order=0, status="approved" if approved else "pending"
    )
    source = SourceExercise(workout_ref=workout, source_name="Puxada", order=0, notes_raw="Controlado")
    normalized = NormalizedExercise(
        source_exercise=source,
        sets_min=3,
        sets_max=3,
        reps_min=12,
        reps_max=12,
        load_value=20,
        load_unit="kg",
        rest_seconds=60,
    )
    mapping = ExerciseMapping(
        source_name="Puxada", template=template, method="manual", confidence=1, confirmed_by_user=confirmed
    )
    db.add_all([template, imported, workout, source, normalized, mapping])
    db.commit()
    return engine, db, imported


def test_payload_requires_approved_workout():
    engine, db, imported = make_db(approved=False)
    result = PayloadBuilderAgent(db).build_payload(imported.id, workout_order=0)
    assert result["blocked"] and result["error"] == "Workout not approved"
    db.close()
    engine.dispose()


def test_payload_builds_deterministic_operation_for_confirmed_import():
    engine, db, imported = make_db()
    first, second = PayloadBuilderAgent(db).build_payload(imported.id, workout_order=0), PayloadBuilderAgent(
        db
    ).build_payload(imported.id, workout_order=0)
    operation = first["operations"][0]
    assert not first["blocked"] and operation["operation_id"] == second["operations"][0]["operation_id"]
    assert (
        operation["payload"]["exercises"][0]["sets"]
        == [{"reps": 12, "weight_kg": 20, "weight_unit": "kg", "rest_seconds": 60}] * 3
    )
    db.close()
    engine.dispose()


def test_payload_can_select_exactly_one_workout():
    engine, db, imported = make_db()
    result = PayloadBuilderAgent(db).build_payload(imported.id, workout_order=0)
    assert len(result["operations"]) == 1
    assert PayloadBuilderAgent(db).build_payload(imported.id, workout_order=99)["blocked"]
    db.close()
    engine.dispose()


def test_write_persists_remote_routine_and_qa_passes():
    engine, db, imported = make_db()

    def handler(request: httpx.Request):
        assert request.headers["api-key"] == "test-key" and request.headers["idempotency-key"]
        return httpx.Response(200, json={"routine": {"id": "remote-1"}}, request=request)

    client = HevyClient(api_key="test-key", transport=httpx.MockTransport(handler))
    plan = PayloadBuilderAgent(db).build_payload(imported.id, workout_order=0)
    result = HevyWriteAgent(db, client).execute_plan(imported.id, plan["operations"])
    assert result["success_count"] == 1 and QAAgent(db).verify_import(imported.id)["all_passed"]
    client.close()
    db.close()
    engine.dispose()


def test_write_failure_marks_import_failed():
    engine, db, imported = make_db()
    client = HevyClient(
        api_key="test-key", transport=httpx.MockTransport(lambda request: httpx.Response(500, request=request))
    )
    result = HevyWriteAgent(db, client).execute_plan(
        imported.id, PayloadBuilderAgent(db).build_payload(imported.id, workout_order=0)["operations"]
    )
    assert result["failure_count"] == 1 and QAAgent(db).verify_import(imported.id)["status"] == "failed"
    client.close()
    db.close()
    engine.dispose()


def test_write_refuses_multiple_workout_operations_without_http_call():
    engine, db, imported = make_db()
    calls = []
    client = HevyClient(
        api_key="test-key",
        transport=httpx.MockTransport(lambda request: calls.append(request) or httpx.Response(200, request=request)),
    )
    operation = PayloadBuilderAgent(db).build_payload(imported.id, workout_order=0)["operations"][0]
    result = HevyWriteAgent(db, client).execute_plan(imported.id, [operation, operation])
    assert result["error"] == "Exactly one workout operation is required"
    assert calls == []
    client.close()
    db.close()
    engine.dispose()
