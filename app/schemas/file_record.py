from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: str
    original_name: str
    mime_type: str | None = None
    extension: str | None = None
    size_bytes: int
    created_at: datetime
