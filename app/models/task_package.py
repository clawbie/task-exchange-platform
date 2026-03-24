from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow


class TaskPackage(Base):
    __tablename__ = "task_packages"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), index=True)
    version: Mapped[int] = mapped_column(default=1)
    manifest_json: Mapped[dict] = mapped_column(JSON, default=dict)
    bundle_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sha256: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_by_actor_id: Mapped[int | None] = mapped_column(ForeignKey("actors.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    task = relationship("Task", back_populates="packages")
