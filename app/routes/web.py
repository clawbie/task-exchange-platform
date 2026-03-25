from pathlib import Path

from fastapi import APIRouter, File, Form, Request, UploadFile, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from app.deps import DbSession
from app.models.actor import Actor
from app.schemas.submission import ReviewDecision, TaskProgressUpdate
from app.services.package_parser import build_task_create_payload
from app.services.tasks import (
    claim_task,
    create_task,
    get_or_create_actor,
    get_task,
    list_task_submissions,
    list_tasks,
    reopen_task,
    review_task_submission,
    submit_task,
    update_task_progress,
)


templates = Jinja2Templates(directory=Path(__file__).resolve().parents[1] / "templates")
router = APIRouter(include_in_schema=False)


@router.get("/")
def home(request: Request, session: DbSession):
    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "tasks": list_tasks(session)[:5],
            "request": request,
        },
    )


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
    title: str = Form(""),
    description: str = Form(""),
    creator_name: str = Form(""),
    creator_type: str = Form(""),
    executor_constraints: str = Form(""),
    reasoning_tier: str = Form(""),
    browser_requirement: str = Form(""),
    compute_requirement: str = Form(""),
    speed_priority: str = Form(""),
    deliverables: str = Form(""),
    acceptance: str = Form(""),
    manifest_file: UploadFile | None = File(default=None),
    attachments: list[UploadFile] | None = File(default=None),
):
    payload = await build_task_create_payload(
        title=title,
        description=description,
        creator_name=creator_name,
        creator_type=creator_type,
        executor_constraints=executor_constraints,
        reasoning_tier=reasoning_tier,
        browser_requirement=browser_requirement,
        compute_requirement=compute_requirement,
        speed_priority=speed_priority,
        deliverables=_split_lines(deliverables),
        acceptance=_split_lines(acceptance),
        manifest_file=manifest_file,
    )
    task = await create_task(session, payload, attachments)
    return RedirectResponse(url=f"/tasks/{task.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/tasks/{task_id}")
def task_detail_page(task_id: str, request: Request, session: DbSession):
    return templates.TemplateResponse(
        request,
        "task_detail.html",
        {
            "submissions": list_task_submissions(session, task_id),
            "task": get_task(session, task_id),
            "request": request,
        },
    )


@router.post("/tasks/{task_id}/claim")
def task_claim_submit(
    task_id: str,
    session: DbSession,
    actor_name: str = Form(...),
    actor_type: str = Form("human"),
):
    actor = get_or_create_actor(session, actor_name, actor_type)
    claim_task(session, task_id, actor)
    return RedirectResponse(url=f"/tasks/{task_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/tasks/{task_id}/progress")
def task_progress_submit(
    task_id: str,
    session: DbSession,
    actor_name: str = Form(...),
    actor_type: str = Form("human"),
    progress_percent: int = Form(...),
    summary: str = Form(""),
):
    actor = get_or_create_actor(session, actor_name, actor_type)
    payload = TaskProgressUpdate(progress_percent=progress_percent, summary=summary or None)
    update_task_progress(session, task_id, actor, payload)
    return RedirectResponse(url=f"/tasks/{task_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/tasks/{task_id}/submit")
async def task_result_submit(
    task_id: str,
    session: DbSession,
    actor_name: str = Form(...),
    actor_type: str = Form("human"),
    summary: str = Form(""),
    result_json: str = Form(""),
    artifacts: list[UploadFile] | None = File(default=None),
):
    actor = get_or_create_actor(session, actor_name, actor_type)
    await submit_task(
        session,
        task_id,
        actor,
        summary=summary or None,
        result_json_text=result_json or None,
        artifacts=artifacts,
    )
    return RedirectResponse(url=f"/tasks/{task_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/tasks/{task_id}/approve")
def task_approve_submit(
    task_id: str,
    session: DbSession,
    actor_name: str = Form(...),
    actor_type: str = Form("human"),
    comment: str = Form(""),
):
    actor = get_or_create_actor(session, actor_name, actor_type)
    review_task_submission(session, task_id, actor, "approved", ReviewDecision(comment=comment or None))
    return RedirectResponse(url=f"/tasks/{task_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/tasks/{task_id}/reject")
def task_reject_submit(
    task_id: str,
    session: DbSession,
    actor_name: str = Form(...),
    actor_type: str = Form("human"),
    comment: str = Form(""),
):
    actor = get_or_create_actor(session, actor_name, actor_type)
    review_task_submission(session, task_id, actor, "rejected", ReviewDecision(comment=comment or None))
    return RedirectResponse(url=f"/tasks/{task_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/tasks/{task_id}/reopen")
def task_reopen_submit(
    task_id: str,
    session: DbSession,
    actor_name: str = Form(...),
    actor_type: str = Form("service"),
    comment: str = Form(""),
):
    actor = get_or_create_actor(session, actor_name, actor_type)
    reopen_task(session, task_id, actor, comment or None)
    return RedirectResponse(url=f"/tasks/{task_id}", status_code=status.HTTP_303_SEE_OTHER)


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


@router.get("/agent")
def agent_guide_page(request: Request):
    return templates.TemplateResponse(request, "agent_guide.html", {"request": request})


@router.get("/agent/runbook")
def agent_runbook_page() -> RedirectResponse:
    return RedirectResponse(url="/agent", status_code=status.HTTP_302_FOUND)


@router.get("/agent/discovery")
def agent_discovery_page() -> RedirectResponse:
    return RedirectResponse(url="/agent", status_code=status.HTTP_302_FOUND)


def _split_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]
