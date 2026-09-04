"""Entidades persistidas pela aplicação MFIT → Hevy."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    """Retorna data UTC sem depender do horário local do servidor."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base declarativa compartilhada por todas as entidades."""


class ExerciseTemplate(Base):
    __tablename__ = "exercise_templates"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    type: Mapped[str | None] = mapped_column(String(64))
    primary_muscle_group: Mapped[str | None] = mapped_column(String(64))
    secondary_muscle_groups: Mapped[str | None] = mapped_column(Text)
    equipment: Mapped[str | None] = mapped_column(String(64))
    is_custom: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    mappings: Mapped[list["ExerciseMapping"]] = relationship(back_populates="template")


class RoutineFolder(Base):
    __tablename__ = "routine_folders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    index: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    routines: Mapped[list["Routine"]] = relationship(back_populates="folder")


class Routine(Base):
    __tablename__ = "routines"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    folder_id: Mapped[int | None] = mapped_column(ForeignKey("routine_folders.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    folder: Mapped[RoutineFolder | None] = relationship(back_populates="routines")


class ExerciseMapping(Base):
    __tablename__ = "exercise_mappings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    normalized_name: Mapped[str | None] = mapped_column(String(255))
    template_id: Mapped[str | None] = mapped_column(ForeignKey("exercise_templates.id"))
    method: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confirmed_by_user: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    template: Mapped[ExerciseTemplate | None] = relationship(back_populates="mappings")

    __table_args__ = (UniqueConstraint("source_name", name="uq_exercise_mapping_source"),)


class Import(Base):
    __tablename__ = "imports"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="received")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    workouts: Mapped[list["SourceWorkout"]] = relationship(back_populates="import_ref", cascade="all, delete-orphan")
    audit_events: Mapped[list["AuditEvent"]] = relationship(back_populates="import_ref", cascade="all, delete-orphan")


class SourceWorkout(Base):
    __tablename__ = "source_workouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    import_id: Mapped[str] = mapped_column(ForeignKey("imports.id"), nullable=False)
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")

    import_ref: Mapped[Import] = relationship(back_populates="workouts")
    exercises: Mapped[list["SourceExercise"]] = relationship(back_populates="workout_ref", cascade="all, delete-orphan")


class SourceExercise(Base):
    __tablename__ = "source_exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workout_id: Mapped[int] = mapped_column(ForeignKey("source_workouts.id"), nullable=False)
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    sets_raw: Mapped[str | None] = mapped_column(String(255))
    reps_raw: Mapped[str | None] = mapped_column(String(255))
    load_raw: Mapped[str | None] = mapped_column(String(255))
    rest_raw: Mapped[str | None] = mapped_column(String(255))
    notes_raw: Mapped[str | None] = mapped_column(Text)
    techniques: Mapped[str | None] = mapped_column(Text)
    group_id: Mapped[int | None] = mapped_column(Integer)
    source_location: Mapped[str | None] = mapped_column(String(255))
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    workout_ref: Mapped[SourceWorkout] = relationship(back_populates="exercises")
    normalized: Mapped["NormalizedExercise | None"] = relationship(
        back_populates="source_exercise", cascade="all, delete-orphan", uselist=False
    )


class NormalizedExercise(Base):
    __tablename__ = "normalized_exercises"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_exercise_id: Mapped[int] = mapped_column(
        ForeignKey("source_exercises.id"), nullable=False, unique=True, index=True
    )
    sets_min: Mapped[int | None] = mapped_column(Integer)
    sets_max: Mapped[int | None] = mapped_column(Integer)
    reps_min: Mapped[int | None] = mapped_column(Integer)
    reps_max: Mapped[int | None] = mapped_column(Integer)
    load_value: Mapped[float | None] = mapped_column(Float)
    load_unit: Mapped[str | None] = mapped_column(String(8))
    rest_seconds: Mapped[int | None] = mapped_column(Integer)
    is_timed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    sets_raw: Mapped[str | None] = mapped_column(String(255))
    reps_raw: Mapped[str | None] = mapped_column(String(255))
    load_raw: Mapped[str | None] = mapped_column(String(255))
    rest_raw: Mapped[str | None] = mapped_column(String(255))
    needs_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    review_reason: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    source_exercise: Mapped[SourceExercise] = relationship(back_populates="normalized")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    import_id: Mapped[str] = mapped_column(ForeignKey("imports.id"), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    agent_version: Mapped[str | None] = mapped_column(String(50))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    input_hash: Mapped[str | None] = mapped_column(String(64))
    output_hash: Mapped[str | None] = mapped_column(String(64))
    warnings: Mapped[str | None] = mapped_column(Text)

    import_ref: Mapped[Import] = relationship(back_populates="audit_events")
