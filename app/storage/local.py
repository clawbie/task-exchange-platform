from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.config import get_settings


def sanitize_filename(name: str) -> str:
    cleaned = Path(name).name.replace(" ", "-")
    return cleaned or f"file-{uuid4().hex[:8]}"


class LocalFileStorage:
    def __init__(self) -> None:
        self.root = Path(get_settings().storage_root)
        self.root.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, upload: UploadFile) -> dict:
        today = datetime.utcnow()
        target_dir = self.root / today.strftime("%Y") / today.strftime("%m") / today.strftime("%d")
        target_dir.mkdir(parents=True, exist_ok=True)

        original_name = sanitize_filename(upload.filename or "upload.bin")
        stored_name = f"{uuid4().hex[:12]}-{original_name}"
        target_path = target_dir / stored_name

        content = await upload.read()
        digest = hashlib.sha256(content).hexdigest()
        target_path.write_bytes(content)
        await upload.close()

        return {
            "original_name": original_name,
            "stored_name": stored_name,
            "mime_type": upload.content_type,
            "extension": target_path.suffix.lower() or None,
            "size_bytes": len(content),
            "storage_path": str(target_path),
            "sha256": digest,
        }
