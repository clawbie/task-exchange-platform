from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile, status

from app.deps import CurrentActor, DbSession
from app.schemas.submission import ReviewDecision, SubmissionRead, TaskProgressUpdate
from app.schemas.task import TaskCreate, TaskListItem, TaskRead
from app.schemas.task_run import TaskRunRead
from app.services.tasks import (
    claim_task,
    create_task,
    get_task,
    list_task_submissions,
    list_tasks,
    review_task_submission,
    submit_task,
    update_task_progress,
)


router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskListItem])
def api_list_tasks(session: DbSession) -> list[TaskListItem]:
    return list_tasks(session)


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def api_create_task(payload: TaskCreate, session: DbSession) -> TaskRead:
    return await create_task(session, payload)


@router.post("/{task_id}/claim", response_model=TaskRunRead)
def api_claim_task(task_id: str, actor: CurrentActor, session: DbSession) -> TaskRunRead:
    return claim_task(session, task_id, actor)


@router.post("/{task_id}/progress", response_model=TaskRunRead)
def api_progress_task(
    task_id: str,
    payload: TaskProgressUpdate,
    actor: CurrentActor,
    session: DbSession,
) -> TaskRunRead:
    return update_task_progress(session, task_id, actor, payload)


@router.post("/{task_id}/submit", response_model=SubmissionRead)
async def api_submit_task(
    task_id: str,
    actor: CurrentActor,
    session: DbSession,
    summary: Annotated[str | None, Form()] = None,
    result_json: Annotated[str | None, Form()] = None,
    artifacts: list[UploadFile] | None = File(default=None),
) -> SubmissionRead:
    return await submit_task(session, task_id, actor, summary, result_json, artifacts)


@router.get("/{task_id}/submissions", response_model=list[SubmissionRead])
def api_list_task_submissions(task_id: str, session: DbSession) -> list[SubmissionRead]:
    return list_task_submissions(session, task_id)


@router.post("/{task_id}/approve", response_model=SubmissionRead)
def api_approve_task(
    task_id: str,
    actor: CurrentActor,
    session: DbSession,
    payload: ReviewDecision | None = None,
) -> SubmissionRead:
    return review_task_submission(session, task_id, actor, "approved", payload)


@router.post("/{task_id}/reject", response_model=SubmissionRead)
def api_reject_task(
    task_id: str,
    actor: CurrentActor,
    session: DbSession,
    payload: ReviewDecision | None = None,
) -> SubmissionRead:
    return review_task_submission(session, task_id, actor, "rejected", payload)


@router.post("/upload", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def api_create_task_with_upload(
    session: DbSession,
    title: Annotated[str, Form(...)],
    description: Annotated[str, Form()] = "",
    creator_name: Annotated[str, Form()] = "",
    creator_type: Annotated[str, Form()] = "human",
    executor_constraints: Annotated[str, Form()] = "human_or_agent",
    reasoning_tier: Annotated[str, Form()] = "medium",
    browser_requirement: Annotated[str, Form()] = "none",
    compute_requirement: Annotated[str, Form()] = "tiny",
    speed_priority: Annotated[str, Form()] = "balanced",
    deliverables: Annotated[str, Form()] = "",
    acceptance: Annotated[str, Form()] = "",
    attachments: list[UploadFile] | None = File(default=None),
) -> TaskRead:
    payload = TaskCreate(
        title=title,
        description=description,
        creator_name=creator_name or None,
        creator_type=creator_type,
        executor_constraints=executor_constraints,
        reasoning_tier=reasoning_tier,
        browser_requirement=browser_requirement,
        compute_requirement=compute_requirement,
        speed_priority=speed_priority,
        deliverables=_split_lines(deliverables),
        acceptance=_split_lines(acceptance),
    )
    return await create_task(session, payload, attachments)


@router.get("/{task_id}", response_model=TaskRead)
def api_get_task(task_id: str, session: DbSession) -> TaskRead:
    return get_task(session, task_id)


def _split_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]
