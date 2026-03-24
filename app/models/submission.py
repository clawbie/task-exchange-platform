from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_run_id: Mapped[int] = mapped_column(ForeignKey("task_runs.id"), index=True)
    submitted_by_actor_id: Mapped[int | None] = mapped_column(ForeignKey("actors.id"), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_json: Mapped[dict] = mapped_column(JSON, default=dict)
    review_status: Mapped[str] = mapped_column(String(32), default="pending")
    reviewed_by_actor_id: Mapped[int | None] = mapped_column(ForeignKey("actors.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    task_run = relationship("TaskRun", back_populates="submissions")
    submitted_by_actor = relationship("Actor", foreign_keys=[submitted_by_actor_id])
    reviewed_by_actor = relationship("Actor", foreign_keys=[reviewed_by_actor_id])
    files = relationship("FileRecord", back_populates="submission")
