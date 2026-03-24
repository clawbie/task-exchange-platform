from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TaskRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: str
    executor_actor_id: int | None = None
    status: str
    progress_percent: int
    started_at: datetime
    ended_at: datetime | None = None
    summary: str | None = None
