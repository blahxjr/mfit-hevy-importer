"""Entidades persistidas pela aplicação MFIT → Hevy."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
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
    media: Mapped["ExerciseTemplateMedia | None"] = relationship(
        back_populates="template",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Exercise(Base):
    """Exercício do catálogo próprio, independente do catálogo Hevy."""

    __tablename__ = "exercises"
    __table_args__ = (UniqueConstraint("exercisedb_id", name="uq_exercises_exercisedb_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    exercisedb_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    hevy_template_id: Mapped[str | None] = mapped_column(ForeignKey("exercise_templates.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name_en: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    body_part: Mapped[str | None] = mapped_column(String(128))
    target_muscle: Mapped[str | None] = mapped_column(String(128))
    secondary_muscles: Mapped[str | None] = mapped_column(Text)
    equipment: Mapped[str | None] = mapped_column(String(128))
    movement_pattern: Mapped[str | None] = mapped_column(String(64), index=True)
    instructions: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(2048))
    video_url: Mapped[str | None] = mapped_column(String(2048))
    media_hint: Mapped[str | None] = mapped_column(String(32))
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="exercisedb", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


class ExerciseTemplateMedia(Base):
    __tablename__ = "exercise_template_media"
    __table_args__ = (
        UniqueConstraint("template_id", name="uq_exercise_template_media_template_id"),
        CheckConstraint(
            "(source = 'placeholder') OR (image_url IS NOT NULL OR local_file_name IS NOT NULL)",
            name="ck_exercise_template_media_has_media",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[str] = mapped_column(ForeignKey("exercise_templates.id"), nullable=False, unique=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    local_file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    alt_text: Mapped[str] = mapped_column(String(255), nullable=False)
    attribution: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    template: Mapped[ExerciseTemplate] = relationship(back_populates="media")


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
    exercise_plan: Mapped[str | None] = mapped_column(Text)
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
    exercise_media: Mapped[list["WorkoutExerciseMedia"]] = relationship(
        back_populates="import_ref", cascade="all, delete-orphan"
    )
    local_workouts: Mapped[list["Workout"]] = relationship(back_populates="import_ref")


class Workout(Base):
    """Treino executável localmente, sem dependência de escrita no Hevy."""

    __tablename__ = "local_workouts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    import_id: Mapped[str | None] = mapped_column(ForeignKey("imports.id"), nullable=True, index=True)
    hevy_workout_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    hevy_routine_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="planned", index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    import_ref: Mapped[Import | None] = relationship(back_populates="local_workouts")
    exercises: Mapped[list["WorkoutExercise"]] = relationship(
        back_populates="workout", cascade="all, delete-orphan", order_by="WorkoutExercise.sequence_index"
    )


class WorkoutExercise(Base):
    __tablename__ = "workout_exercises"
    __table_args__ = (UniqueConstraint("workout_id", "sequence_index", name="uq_workout_exercise_sequence"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workout_id: Mapped[str] = mapped_column(ForeignKey("local_workouts.id", ondelete="CASCADE"), nullable=False, index=True)
    exercise_id: Mapped[str] = mapped_column(ForeignKey("exercises.id"), nullable=False, index=True)
    sequence_index: Mapped[int] = mapped_column(Integer, nullable=False)
    planned_sets: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    planned_reps: Mapped[int | None] = mapped_column(Integer)
    planned_load: Mapped[str | None] = mapped_column(String(64))
    planned_time_seconds: Mapped[int | None] = mapped_column(Integer)
    planned_distance_meters: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    workout: Mapped[Workout] = relationship(back_populates="exercises")
    exercise: Mapped[Exercise] = relationship()
    set_logs: Mapped[list["WorkoutSetLog"]] = relationship(
        back_populates="workout_exercise", cascade="all, delete-orphan", order_by="WorkoutSetLog.set_index"
    )


class WorkoutSetLog(Base):
    __tablename__ = "workout_set_logs"
    __table_args__ = (UniqueConstraint("workout_exercise_id", "set_index", name="uq_workout_set_log_index"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workout_exercise_id: Mapped[str] = mapped_column(ForeignKey("workout_exercises.id", ondelete="CASCADE"), nullable=False, index=True)
    set_index: Mapped[int] = mapped_column(Integer, nullable=False)
    actual_reps: Mapped[int | None] = mapped_column(Integer)
    actual_load: Mapped[str | None] = mapped_column(String(64))
    actual_time_seconds: Mapped[int | None] = mapped_column(Integer)
    actual_distance_meters: Mapped[int | None] = mapped_column(Integer)
    rpe: Mapped[int | None] = mapped_column(Integer)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    workout_exercise: Mapped[WorkoutExercise] = relationship(back_populates="set_logs")


class WorkoutExerciseMedia(Base):
    __tablename__ = "workout_exercise_media"
    __table_args__ = (
        UniqueConstraint("import_id", "exercise_index", name="uq_workout_exercise_media_import_index"),
        CheckConstraint(
            "(source = 'placeholder') OR (image_url IS NOT NULL OR local_file_name IS NOT NULL)",
            name="ck_workout_exercise_media_has_media",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    import_id: Mapped[str] = mapped_column(ForeignKey("imports.id"), nullable=False)
    exercise_index: Mapped[int] = mapped_column(Integer, nullable=False)
    template_id: Mapped[str | None] = mapped_column(ForeignKey("exercise_templates.id"), nullable=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    local_file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    alt_text: Mapped[str] = mapped_column(String(255), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    import_ref: Mapped[Import] = relationship(back_populates="exercise_media")
    template: Mapped[ExerciseTemplate | None] = relationship()


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
    canonicalization: Mapped["ExerciseCanonicalization | None"] = relationship(
        back_populates="source_exercise", cascade="all, delete-orphan", uselist=False
    )


class ExerciseCanonicalization(Base):
    __tablename__ = "exercise_canonicalizations"
    __table_args__ = (
        UniqueConstraint(
            "source_exercise_id",
            name="uq_exercise_canonicalizations_source_exercise_id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_exercise_id: Mapped[int] = mapped_column(ForeignKey("source_exercises.id"), nullable=False)
    source_name_pt: Mapped[str] = mapped_column(String(255), nullable=False)
    canonical_name_en: Mapped[str | None] = mapped_column(String(255), index=True)
    search_aliases_en: Mapped[str | None] = mapped_column(Text)
    movement_pattern: Mapped[str | None] = mapped_column(String(64))
    equipment_hint: Mapped[str | None] = mapped_column(String(64))
    primary_muscle_hint: Mapped[str | None] = mapped_column(String(128))
    secondary_muscles_hint: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    needs_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    review_reason: Mapped[str | None] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(64), nullable=False, default="external_ai")
    model_name: Mapped[str | None] = mapped_column(String(128))
    prompt_version: Mapped[str] = mapped_column(String(32), nullable=False, default="v1")
    raw_response_sanitized: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    source_exercise: Mapped[SourceExercise] = relationship(back_populates="canonicalization")


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
