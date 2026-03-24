from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.actor import ActorRead
from app.schemas.enums import BrowserRequirement, ComputeRequirement, ExecutorConstraints, ReasoningTier, SpeedPriority
from app.schemas.file_record import FileRead


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    creator_name: str | None = None
    creator_type: str = "human"
    executor_constraints: ExecutorConstraints = ExecutorConstraints.HUMAN_OR_AGENT
    reasoning_tier: ReasoningTier = ReasoningTier.MEDIUM
    browser_requirement: BrowserRequirement = BrowserRequirement.NONE
    compute_requirement: ComputeRequirement = ComputeRequirement.TINY
    speed_priority: SpeedPriority = SpeedPriority.BALANCED
    deliverables: list[str] = Field(default_factory=list)
    acceptance: list[str] = Field(default_factory=list)


class TaskListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    status: str
    executor_constraints: ExecutorConstraints
    reasoning_tier: ReasoningTier
    browser_requirement: BrowserRequirement
    compute_requirement: ComputeRequirement
    speed_priority: SpeedPriority
    updated_at: datetime


class TaskRead(TaskListItem):
    description: str
    deliverables: list[str]
    acceptance: list[str]
    created_at: datetime
    created_by_actor: ActorRead | None = None
    assigned_to_actor: ActorRead | None = None
    files: list[FileRead] = Field(default_factory=list)
