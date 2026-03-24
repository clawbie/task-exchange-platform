from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow


class FileRecord(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[str | None] = mapped_column(ForeignKey("tasks.id"), nullable=True, index=True)
    run_id: Mapped[int | None] = mapped_column(ForeignKey("task_runs.id"), nullable=True)
    submission_id: Mapped[int | None] = mapped_column(ForeignKey("submissions.id"), nullable=True)
    uploaded_by_actor_id: Mapped[int | None] = mapped_column(ForeignKey("actors.id"), nullable=True)
    kind: Mapped[str] = mapped_column(String(32), default="task_attachment")
    original_name: Mapped[str] = mapped_column(String(260))
    stored_name: Mapped[str] = mapped_column(String(260))
    mime_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    extension: Mapped[str | None] = mapped_column(String(32), nullable=True)
    size_bytes: Mapped[int] = mapped_column(default=0)
    storage_path: Mapped[str] = mapped_column(String(500))
    sha256: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    task = relationship("Task", back_populates="files")
