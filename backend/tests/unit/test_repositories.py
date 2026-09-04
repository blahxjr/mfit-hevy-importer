import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from src.domain.models import (
    AuditEvent,
    Base,
    ExerciseMapping,
    ExerciseTemplate,
    Import,
    Routine,
    RoutineFolder,
    SourceExercise,
    SourceWorkout,
)
from src.repositories.exercise_mapping_repository import ExerciseMappingRepository
from src.repositories.exercise_template_repository import ExerciseTemplateRepository
from src.repositories.import_repository import ImportRepository
from src.repositories.routine_folder_repository import RoutineFolderRepository
from src.repositories.routine_repository import RoutineRepository
from src.repositories.source_exercise_repository import SourceExerciseRepository
from src.repositories.source_workout_repository import SourceWorkoutRepository


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    engine.dispose()


def test_exercise_template_repository_save_and_find(db_session):
    repository = ExerciseTemplateRepository(db_session)
    saved = repository.save(ExerciseTemplate(id="template-123", title="Supino Reto", type="strength"))

    assert saved.id == "template-123"
    assert repository.get_by_id("template-123") is saved
    assert repository.get_by_title("Supino Reto") is saved
    assert repository.get_all() == [saved]


def test_mapping_repository_enforces_unique_source_name(db_session):
    template = ExerciseTemplate(id="template-123", title="Supino Reto")
    db_session.add(template)
    db_session.commit()
    repository = ExerciseMappingRepository(db_session)
    mapping = repository.save(
        ExerciseMapping(source_name="Supino", template_id=template.id, method="exact", confirmed_by_user=True)
    )

    assert repository.get_by_source_name("Supino") is mapping
    assert repository.get_confirmed() == [mapping]
    db_session.add(ExerciseMapping(source_name="Supino", method="manual"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_folder_and_routine_repositories_keep_remote_identifier_types(db_session):
    folder = RoutineFolderRepository(db_session).save(RoutineFolder(id=42, title="Força", index=0))
    routine = RoutineRepository(db_session).save(Routine(id="hevy-routine-id", title="Treino A", folder_id=folder.id))

    assert RoutineFolderRepository(db_session).get_by_id(42).title == "Força"
    assert RoutineRepository(db_session).get_by_id("hevy-routine-id") is routine
    assert routine.folder is folder


def test_import_graph_repositories_and_cascade_delete(db_session):
    import_repository = ImportRepository(db_session)
    imported = Import(id="import-1", filename="ficha.pdf", sha256="a" * 64)
    saved_import = import_repository.save(imported)
    workout = SourceWorkoutRepository(db_session).save(
        SourceWorkout(import_id=saved_import.id, source_name="Treino A", order=1)
    )
    exercise = SourceExerciseRepository(db_session).save(
        SourceExercise(workout_id=workout.id, source_name="Supino", order=1)
    )
    db_session.add(AuditEvent(import_id=saved_import.id, agent_name="parser"))
    db_session.commit()

    assert import_repository.get_by_sha256("a" * 64) is saved_import
    assert SourceWorkoutRepository(db_session).get_by_import_id(saved_import.id) == [workout]
    assert SourceExerciseRepository(db_session).get_by_workout_id(workout.id) == [exercise]

    import_repository.delete(saved_import)
    assert db_session.query(SourceWorkout).count() == 0
    assert db_session.query(SourceExercise).count() == 0
    assert db_session.query(AuditEvent).count() == 0
