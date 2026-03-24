from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from app.config import get_settings
from app.db import check_database_connection


router = APIRouter(tags=["system"])


@router.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz")
def readyz() -> dict[str, str]:
    settings = get_settings()

    try:
        check_database_connection()
        Path(settings.storage_root).mkdir(parents=True, exist_ok=True)
    except Exception as exc:  # pragma: no cover - exercised through integration tests
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service dependencies are not ready",
        ) from exc

    return {"status": "ready"}
