from __future__ import annotations

from typing import Any

import yaml
from fastapi import HTTPException, UploadFile, status

from app.schemas.task import TaskCreate


async def build_task_create_payload(
    *,
    title: str = "",
    description: str = "",
    creator_name: str = "",
    creator_type: str = "human",
    executor_constraints: str = "human_or_agent",
    reasoning_tier: str = "medium",
    browser_requirement: str = "none",
    compute_requirement: str = "tiny",
    speed_priority: str = "balanced",
    deliverables: list[str] | None = None,
    acceptance: list[str] | None = None,
    manifest_file: UploadFile | None = None,
) -> TaskCreate:
    manifest_data = await _parse_manifest_file(manifest_file) if manifest_file and manifest_file.filename else {}

    payload_data = {
        "title": manifest_data.get("title", ""),
        "description": manifest_data.get("description", ""),
        "creator_name": manifest_data.get("creator_name"),
        "creator_type": manifest_data.get("creator_type", "human"),
        "executor_constraints": manifest_data.get("executor_constraints", "human_or_agent"),
        "reasoning_tier": manifest_data.get("reasoning_tier", "medium"),
        "browser_requirement": manifest_data.get("browser_requirement", "none"),
        "compute_requirement": manifest_data.get("compute_requirement", "tiny"),
        "speed_priority": manifest_data.get("speed_priority", "balanced"),
        "deliverables": _normalize_list(manifest_data.get("deliverables")),
        "acceptance": _normalize_list(manifest_data.get("acceptance")),
    }

    if title:
        payload_data["title"] = title
    if description:
        payload_data["description"] = description
    if creator_name:
        payload_data["creator_name"] = creator_name
    if creator_type:
        payload_data["creator_type"] = creator_type
    if executor_constraints:
        payload_data["executor_constraints"] = executor_constraints
    if reasoning_tier:
        payload_data["reasoning_tier"] = reasoning_tier
    if browser_requirement:
        payload_data["browser_requirement"] = browser_requirement
    if compute_requirement:
        payload_data["compute_requirement"] = compute_requirement
    if speed_priority:
        payload_data["speed_priority"] = speed_priority
    if deliverables:
        payload_data["deliverables"] = deliverables
    if acceptance:
        payload_data["acceptance"] = acceptance

    return TaskCreate(**payload_data)


async def _parse_manifest_file(manifest_file: UploadFile) -> dict[str, Any]:
    raw = await manifest_file.read()
    await manifest_file.close()

    try:
        data = yaml.safe_load(raw.decode("utf-8")) or {}
    except Exception as exc:  # pragma: no cover - defensive parse guard
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid manifest.yaml file") from exc

    if not isinstance(data, dict):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="manifest.yaml must contain an object")

    return data


def _normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []
