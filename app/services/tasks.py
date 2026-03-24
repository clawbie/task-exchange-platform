from __future__ import annotations

import json
from typing import Iterable

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.actor import Actor
from app.models.event import Event
from app.models.file_record import FileRecord
from app.models.base import utcnow
from app.models.submission import Submission
from app.models.task import Task
from app.models.task_package import TaskPackage
from app.models.task_run import TaskRun
from app.schemas.submission import ReviewDecision, TaskProgressUpdate
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


def list_task_submissions(session: Session, task_id: str) -> list[Submission]:
    stmt = (
        select(Submission)
        .join(TaskRun, Submission.task_run_id == TaskRun.id)
        .where(TaskRun.task_id == task_id)
        .options(selectinload(Submission.files))
        .order_by(Submission.created_at.desc())
    )
    return list(session.scalars(stmt).all())


def get_latest_submission(session: Session, task_id: str) -> Submission:
    stmt = (
        select(Submission)
        .join(TaskRun, Submission.task_run_id == TaskRun.id)
        .where(TaskRun.task_id == task_id)
        .options(selectinload(Submission.files))
        .order_by(Submission.created_at.desc())
    )
    submission = session.scalar(stmt)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    return submission


async def create_task(
    session: Session,
    payload: TaskCreate,
    attachments: Iterable[UploadFile] | None = None,
) -> Task:
    attachment_items = list(attachments or [])
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

    session.add(
        TaskPackage(
            task_id=task.id,
            version=1,
            manifest_json=_build_task_manifest(payload, attachment_items),
            created_by_actor_id=creator.id if creator else None,
        )
    )

    storage = LocalFileStorage()
    for upload in attachment_items:
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


def claim_task(session: Session, task_id: str, actor: Actor) -> TaskRun:
    task = get_task(session, task_id)
    _assert_actor_can_execute(task, actor)

    if task.status in {"approved", "rejected", "cancelled", "archived"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Task is not claimable")

    if task.assigned_to_actor_id and task.assigned_to_actor_id != actor.id and task.status in {"claimed", "running", "submitted"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Task is already assigned")

    existing_run = session.scalar(
        select(TaskRun)
        .where(
            TaskRun.task_id == task_id,
            TaskRun.executor_actor_id == actor.id,
            TaskRun.status.in_(["claimed", "running"]),
        )
        .order_by(TaskRun.id.desc())
    )
    if existing_run:
        return existing_run

    run = TaskRun(
        task_id=task.id,
        executor_actor_id=actor.id,
        status="claimed",
        progress_percent=0,
    )
    task.assigned_to_actor_id = actor.id
    task.status = "claimed"
    session.add(run)
    session.flush()
    session.add(
        Event(
            task_id=task.id,
            run_id=run.id,
            actor_id=actor.id,
            event_type="task_claimed",
            payload_json={"actor_name": actor.name},
        )
    )
    session.commit()
    session.refresh(run)
    return run


def update_task_progress(session: Session, task_id: str, actor: Actor, payload: TaskProgressUpdate) -> TaskRun:
    task = get_task(session, task_id)
    run = _get_active_run(session, task_id, actor.id)
    run.status = "running"
    run.progress_percent = payload.progress_percent
    if payload.summary is not None:
        run.summary = payload.summary
    task.status = "running"
    task.assigned_to_actor_id = actor.id
    session.add(
        Event(
            task_id=task.id,
            run_id=run.id,
            actor_id=actor.id,
            event_type="task_progress_updated",
            payload_json={
                "progress_percent": payload.progress_percent,
                "summary": payload.summary,
            },
        )
    )
    session.commit()
    session.refresh(run)
    return run


async def submit_task(
    session: Session,
    task_id: str,
    actor: Actor,
    summary: str | None,
    result_json_text: str | None,
    artifacts: Iterable[UploadFile] | None = None,
) -> Submission:
    task = get_task(session, task_id)
    run = _get_active_run(session, task_id, actor.id)

    try:
        result_json = json.loads(result_json_text) if result_json_text else {}
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid result_json payload") from exc

    submission = Submission(
        task_run_id=run.id,
        submitted_by_actor_id=actor.id,
        summary=summary,
        result_json=result_json,
        review_status="pending",
    )
    session.add(submission)
    session.flush()

    storage = LocalFileStorage()
    artifact_count = 0
    for upload in artifacts or []:
        if not upload.filename:
            continue
        artifact_count += 1
        stored = await storage.save_upload(upload)
        session.add(
            FileRecord(
                task_id=task.id,
                run_id=run.id,
                submission_id=submission.id,
                uploaded_by_actor_id=actor.id,
                kind="submission_artifact",
                original_name=stored["original_name"],
                stored_name=stored["stored_name"],
                mime_type=stored["mime_type"],
                extension=stored["extension"],
                size_bytes=stored["size_bytes"],
                storage_path=stored["storage_path"],
                sha256=stored["sha256"],
            )
        )

    run.status = "submitted"
    run.summary = summary or run.summary
    run.ended_at = utcnow()
    task.status = "submitted"
    task.assigned_to_actor_id = actor.id
    session.add(
        Event(
            task_id=task.id,
            run_id=run.id,
            actor_id=actor.id,
            event_type="task_submitted",
            payload_json={
                "artifact_count": artifact_count,
                "summary": summary,
            },
        )
    )
    session.commit()
    return _get_submission_by_id(session, submission.id)


def review_task_submission(
    session: Session,
    task_id: str,
    actor: Actor,
    decision: str,
    payload: ReviewDecision | None = None,
) -> Submission:
    task = get_task(session, task_id)
    submission = get_latest_submission(session, task_id)
    if submission.review_status in {"approved", "rejected"}:
        return submission

    submission.review_status = decision
    submission.reviewed_by_actor_id = actor.id
    submission.reviewed_at = utcnow()
    submission.task_run.status = decision
    task.status = decision
    session.add(
        Event(
            task_id=task.id,
            run_id=submission.task_run_id,
            actor_id=actor.id,
            event_type="task_reviewed",
            payload_json={
                "decision": decision,
                "comment": payload.comment if payload else None,
            },
        )
    )
    session.commit()
    return _get_submission_by_id(session, submission.id)


def _get_active_run(session: Session, task_id: str, actor_id: int) -> TaskRun:
    run = session.scalar(
        select(TaskRun)
        .where(
            TaskRun.task_id == task_id,
            TaskRun.executor_actor_id == actor_id,
            TaskRun.status.in_(["claimed", "running"]),
        )
        .order_by(TaskRun.id.desc())
    )
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active run not found")
    return run


def _get_submission_by_id(session: Session, submission_id: int) -> Submission:
    stmt = select(Submission).where(Submission.id == submission_id).options(selectinload(Submission.files))
    submission = session.scalar(stmt)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    return submission


def _assert_actor_can_execute(task: Task, actor: Actor) -> None:
    if task.executor_constraints == "human_only" and actor.type != "human":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Task requires a human executor")
    if task.executor_constraints == "agent_only" and actor.type not in {"agent", "service"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Task requires an agent executor")


def _build_task_manifest(payload: TaskCreate, attachments: list[UploadFile]) -> dict:
    return {
        "title": payload.title,
        "description": payload.description,
        "creator_name": payload.creator_name,
        "creator_type": payload.creator_type,
        "executor_constraints": payload.executor_constraints.value,
        "reasoning_tier": payload.reasoning_tier.value,
        "browser_requirement": payload.browser_requirement.value,
        "compute_requirement": payload.compute_requirement.value,
        "speed_priority": payload.speed_priority.value,
        "deliverables": payload.deliverables,
        "acceptance": payload.acceptance,
        "attachments": [upload.filename for upload in attachments if upload.filename],
    }
