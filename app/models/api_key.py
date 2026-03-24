from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("actors.id"), index=True)
    label: Mapped[str] = mapped_column(String(120), default="default")
    key_prefix: Mapped[str] = mapped_column(String(32), index=True)
    key_hash: Mapped[str] = mapped_column(String(128), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    actor = relationship("Actor", back_populates="api_keys")
