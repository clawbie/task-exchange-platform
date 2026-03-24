from __future__ import annotations

from typing import Iterable

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.actor import Actor
from app.models.event import Event
from app.models.file_record import FileRecord
from app.models.task import Task
from app.schemas.task import TaskCreate
from app.storage.local import LocalFileStorage


def get_or_create_actor(session: Session, name: str, actor_type: str = "human") -> Actor:
    existing = session.scalar(
        select(Actor).where(
            Actor.name == name,
            Actor.type == actor_type,
        )
    )
    if existing:
        return existing

    actor = Actor(name=name, type=actor_type)
    session.add(actor)
    session.flush()
    return actor


def list_tasks(session: Session) -> list[Task]:
    stmt = (
        select(Task)
        .options(
            selectinload(Task.created_by_actor),
            selectinload(Task.assigned_to_actor),
            selectinload(Task.files),
        )
        .order_by(Task.updated_at.desc())
    )
    return list(session.scalars(stmt).all())


def get_task(session: Session, task_id: str) -> Task:
    stmt = (
        select(Task)
        .where(Task.id == task_id)
        .options(
            selectinload(Task.created_by_actor),
            selectinload(Task.assigned_to_actor),
            selectinload(Task.files),
            selectinload(Task.events),
        )
    )
    task = session.scalar(stmt)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


async def create_task(
    session: Session,
    payload: TaskCreate,
    attachments: Iterable[UploadFile] | None = None,
) -> Task:
    creator = None
    if payload.creator_name:
        creator = get_or_create_actor(session, payload.creator_name, payload.creator_type)

    task = Task(
        title=payload.title,
        description=payload.description,
        status="published",
        created_by_actor_id=creator.id if creator else None,
        executor_constraints=payload.executor_constraints.value,
        reasoning_tier=payload.reasoning_tier.value,
        browser_requirement=payload.browser_requirement.value,
        compute_requirement=payload.compute_requirement.value,
        speed_priority=payload.speed_priority.value,
        deliverables=payload.deliverables,
        acceptance=payload.acceptance,
    )
    session.add(task)
    session.flush()

    storage = LocalFileStorage()
    for upload in attachments or []:
        if not upload.filename:
            continue
        stored = await storage.save_upload(upload)
        session.add(
            FileRecord(
                task_id=task.id,
                uploaded_by_actor_id=creator.id if creator else None,
                kind="task_attachment",
                original_name=stored["original_name"],
                stored_name=stored["stored_name"],
                mime_type=stored["mime_type"],
                extension=stored["extension"],
                size_bytes=stored["size_bytes"],
                storage_path=stored["storage_path"],
                sha256=stored["sha256"],
            )
        )

    session.add(
        Event(
            task_id=task.id,
            actor_id=creator.id if creator else None,
            event_type="task_created",
            payload_json={
                "title": payload.title,
                "creator_name": payload.creator_name,
            },
        )
    )
    session.commit()
    return get_task(session, task.id)
