from pathlib import Path

from fastapi import APIRouter, File, Form, Request, UploadFile, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from app.deps import DbSession
from app.models.actor import Actor
from app.schemas.task import TaskCreate
from app.services.tasks import create_task, get_task, list_tasks


templates = Jinja2Templates(directory=Path(__file__).resolve().parents[1] / "templates")
router = APIRouter(include_in_schema=False)


@router.get("/")
def home() -> RedirectResponse:
    return RedirectResponse(url="/tasks", status_code=status.HTTP_302_FOUND)


@router.get("/tasks")
def tasks_page(request: Request, session: DbSession):
    return templates.TemplateResponse(
        request,
        "tasks_list.html",
        {
            "tasks": list_tasks(session),
            "request": request,
        },
    )


@router.get("/tasks/new")
def task_new_page(request: Request):
    return templates.TemplateResponse(request, "task_new.html", {"request": request})


@router.post("/tasks/new")
async def task_new_submit(
    request: Request,
    session: DbSession,
    title: str = Form(...),
    description: str = Form(""),
    creator_name: str = Form(""),
    creator_type: str = Form("human"),
    executor_constraints: str = Form("human_or_agent"),
    reasoning_tier: str = Form("medium"),
    browser_requirement: str = Form("none"),
    compute_requirement: str = Form("tiny"),
    speed_priority: str = Form("balanced"),
    deliverables: str = Form(""),
    acceptance: str = Form(""),
    attachments: list[UploadFile] | None = File(default=None),
):
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
    task = await create_task(session, payload, attachments)
    return RedirectResponse(url=f"/tasks/{task.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/tasks/{task_id}")
def task_detail_page(task_id: str, request: Request, session: DbSession):
    return templates.TemplateResponse(
        request,
        "task_detail.html",
        {
            "task": get_task(session, task_id),
            "request": request,
        },
    )


@router.get("/actors")
def actors_page(request: Request, session: DbSession):
    actors = list(session.scalars(select(Actor).order_by(Actor.created_at.desc())).all())
    return templates.TemplateResponse(
        request,
        "actors_list.html",
        {
            "actors": actors,
            "request": request,
        },
    )


def _split_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]
