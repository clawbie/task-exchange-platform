from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.actor import ActorRead
from app.schemas.enums import ActorType


class ApiKeyCreateRequest(BaseModel):
    actor_name: str = Field(min_length=1, max_length=120)
    actor_type: ActorType = ActorType.AGENT
    label: str = Field(default="default", min_length=1, max_length=120)


class ApiKeyCreateResponse(BaseModel):
    actor: ActorRead
    api_key: str
    key_prefix: str
    label: str
    created_at: datetime


class ApiKeyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    label: str
    key_prefix: str
    created_at: datetime
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None
