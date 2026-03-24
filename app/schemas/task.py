from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.actor import ActorRead
from app.schemas.enums import ActorType, BrowserRequirement, ComputeRequirement, ExecutorConstraints, ReasoningTier, SpeedPriority
from app.schemas.event import EventRead
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

    @model_validator(mode="after")
    def validate_agent_task_requirements(self):
        if self.creator_type in {ActorType.AGENT.value, ActorType.SERVICE.value}:
            if not (self.creator_name or "").strip():
                raise ValueError("creator_name is required for agent/service tasks")
            if not self.description.strip():
                raise ValueError("description is required for agent/service tasks")
            if not self.deliverables:
                raise ValueError("deliverables are required for agent/service tasks")
            if not self.acceptance:
                raise ValueError("acceptance criteria are required for agent/service tasks")
        return self


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
    events: list[EventRead] = Field(default_factory=list)
