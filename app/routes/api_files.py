from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.deps import DbSession
from app.models.file_record import FileRecord


router = APIRouter(prefix="/api/files", tags=["files"])


@router.get("/{file_id}/download")
def download_file(file_id: int, session: DbSession) -> FileResponse:
    file_record = session.scalar(select(FileRecord).where(FileRecord.id == file_id))
    if not file_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    path = Path(file_record.storage_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored file missing")

    return FileResponse(
        path=path,
        media_type=file_record.mime_type or "application/octet-stream",
        filename=file_record.original_name,
    )
