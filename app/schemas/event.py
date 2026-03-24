from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: str
    run_id: int | None = None
    actor_id: int | None = None
    event_type: str
    payload_json: dict
    created_at: datetime
