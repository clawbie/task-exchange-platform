from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow


class Actor(Base):
    __tablename__ = "actors"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(32), default="human", index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    status: Mapped[str] = mapped_column(String(32), default="active")
    reasoning_tier: Mapped[str] = mapped_column(String(32), default="medium")
    browser_capability: Mapped[str] = mapped_column(String(32), default="none")
    compute_capacity: Mapped[str] = mapped_column(String(32), default="tiny")
    speed_tier: Mapped[str] = mapped_column(String(32), default="balanced")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    created_tasks = relationship(
        "Task",
        foreign_keys="Task.created_by_actor_id",
        back_populates="created_by_actor",
    )
    assigned_tasks = relationship(
        "Task",
        foreign_keys="Task.assigned_to_actor_id",
        back_populates="assigned_to_actor",
    )
