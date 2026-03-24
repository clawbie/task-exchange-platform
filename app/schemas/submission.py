from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.file_record import FileRead


class TaskProgressUpdate(BaseModel):
    progress_percent: int = Field(ge=0, le=100)
    summary: str | None = None


class SubmissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_run_id: int
    submitted_by_actor_id: int | None = None
    summary: str | None = None
    result_json: dict
    review_status: str
    reviewed_by_actor_id: int | None = None
    reviewed_at: datetime | None = None
    created_at: datetime
    files: list[FileRead] = Field(default_factory=list)


class ReviewDecision(BaseModel):
    comment: str | None = None
