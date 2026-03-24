from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.enums import ActorType, BrowserRequirement, ComputeRequirement, ReasoningTier, SpeedPriority


class ActorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: ActorType
    name: str
    status: str
    reasoning_tier: ReasoningTier
    browser_capability: BrowserRequirement
    compute_capacity: ComputeRequirement
    speed_tier: SpeedPriority
    last_seen_at: datetime | None = None
    created_at: datetime
