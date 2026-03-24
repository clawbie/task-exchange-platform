from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow


def make_task_id() -> str:
    return f"task-{uuid4().hex[:10]}"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=make_task_id)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="published", index=True)
    created_by_actor_id: Mapped[int | None] = mapped_column(ForeignKey("actors.id"), nullable=True)
    assigned_to_actor_id: Mapped[int | None] = mapped_column(ForeignKey("actors.id"), nullable=True)
    executor_constraints: Mapped[str] = mapped_column(String(32), default="human_or_agent")
    reasoning_tier: Mapped[str] = mapped_column(String(32), default="medium")
    browser_requirement: Mapped[str] = mapped_column(String(32), default="none")
    compute_requirement: Mapped[str] = mapped_column(String(32), default="tiny")
    speed_priority: Mapped[str] = mapped_column(String(32), default="balanced")
    deliverables: Mapped[list[str]] = mapped_column(JSON, default=list)
    acceptance: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    created_by_actor = relationship("Actor", foreign_keys=[created_by_actor_id], back_populates="created_tasks")
    assigned_to_actor = relationship("Actor", foreign_keys=[assigned_to_actor_id], back_populates="assigned_tasks")
    files = relationship("FileRecord", back_populates="task", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="task", cascade="all, delete-orphan")
    packages = relationship("TaskPackage", back_populates="task", cascade="all, delete-orphan")
    runs = relationship("TaskRun", back_populates="task", cascade="all, delete-orphan")
