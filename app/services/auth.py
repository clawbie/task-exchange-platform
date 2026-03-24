from __future__ import annotations

import hashlib
import secrets
from hmac import compare_digest

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.api_key import ApiKey
from app.models.base import utcnow
from app.models.actor import Actor
from app.services.tasks import get_or_create_actor


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def _key_prefix(raw_key: str) -> str:
    return raw_key[:16]


def generate_api_key_value() -> str:
    return f"txp_{secrets.token_urlsafe(24)}"


def create_api_key(session: Session, actor_name: str, actor_type: str, label: str) -> tuple[Actor, ApiKey, str]:
    actor = get_or_create_actor(session, actor_name, actor_type)
    raw_key = generate_api_key_value()
    api_key = ApiKey(
        actor_id=actor.id,
        label=label,
        key_prefix=_key_prefix(raw_key),
        key_hash=_hash_key(raw_key),
    )
    session.add(api_key)
    session.commit()
    session.refresh(actor)
    session.refresh(api_key)
    return actor, api_key, raw_key


def authenticate_api_key(session: Session, presented_key: str) -> Actor | None:
    api_key = session.scalar(
        select(ApiKey).where(
            ApiKey.key_prefix == _key_prefix(presented_key),
            ApiKey.revoked_at.is_(None),
        )
    )
    if not api_key:
        return None

    if not compare_digest(api_key.key_hash, _hash_key(presented_key)):
        return None

    api_key.last_used_at = utcnow()
    session.commit()
    return session.get(Actor, api_key.actor_id)
