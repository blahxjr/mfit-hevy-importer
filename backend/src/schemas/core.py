"""
Core schemas for orchestration state and data flow
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Any
from enum import Enum
from datetime import datetime


class ImportStatus(str, Enum):
    """Status of an import process"""
    RECEIVED = "received"
    PARSED = "parsed"
    NORMALIZED = "normalized"
    MAPPED = "mapped"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED = "approved"
    WRITING = "writing"
    COMPLETED = "completed"
    FAILED = "failed"


class Source(BaseModel):
    """Source file information"""
    filename: str
    sha256: str
    type: str = Field(..., description="pdf or image")


class ExerciseConfidence(BaseModel):
    """Confidence metadata for fields"""
    field: str
    value: float = Field(..., ge=0.0, le=1.0)
    reason: Optional[str] = None


class SourceExercise(BaseModel):
    """Original exercise as extracted from source"""
    source_name: str
    order: int
    sets_raw: str
    reps_raw: str
    load_raw: str
    rest_raw: str
    notes_raw: Optional[str] = None
    techniques: List[str] = []
    group_id: Optional[str] = None
    source_location: str = Field(default="", description="page and position")
    confidence: float = 0.0
    warnings: List[str] = []


class SourceWorkout(BaseModel):
    """Workout as extracted from source"""
    source_name: str
    order: int
    exercises: List[SourceExercise]


class MappingDecision(BaseModel):
    """Mapping decision with audit trail"""
    source_exercise_name: str
    hevy_template_id: str
    hevy_template_title: str
    method: str = Field(..., description="memory|exact|alias|fuzzy|manual|none")
    confidence: float
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    reason: Optional[str] = None


class PlannedOperation(BaseModel):
    """Operation to be executed on Hevy"""
    operation_id: str
    type: str = Field(..., description="create_folder|create_routine|update_routine")
    endpoint: str
    idempotency_key: str
    payload: dict = Field(default_factory=dict)
    risk: str = "low"
    validation_errors: List[str] = []


class ImportState(BaseModel):
    """Complete state of an import process"""
    project_id: str
    import_id: str
    status: ImportStatus
    source: Source
    workouts: List[SourceWorkout] = []
    mapping_decisions: List[MappingDecision] = []
    planned_operations: List[PlannedOperation] = []
    approval: Optional[dict] = None
    memory_refs: List[str] = []
    errors: List[str] = []
    audit_events: List[dict] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AgentResponse(BaseModel):
    """Standard response from any agent"""
    status: str = Field(..., description="CONTINUE|REVIEW_REQUIRED|APPROVAL_REQUIRED|COMPLETED|FAILED")
    current_stage: str
    facts: List[str] = []
    decisions: List[str] = []
    agent_calls: List[dict] = []
    warnings: List[str] = []
    questions: List[str] = []
    next_action: str
    output_hash: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
