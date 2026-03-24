from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile, status

from app.deps import DbSession
from app.schemas.task import TaskCreate, TaskListItem, TaskRead
from app.services.tasks import create_task, get_task, list_tasks


router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskListItem])
def api_list_tasks(session: DbSession) -> list[TaskListItem]:
    return list_tasks(session)


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def api_create_task(payload: TaskCreate, session: DbSession) -> TaskRead:
    return await create_task(session, payload)


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
