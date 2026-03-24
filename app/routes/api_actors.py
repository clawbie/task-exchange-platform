from fastapi import APIRouter
from sqlalchemy import select

from app.deps import CurrentActor, DbSession
from app.models.actor import Actor
from app.schemas.actor import ActorRead
from app.schemas.api_key import ApiKeyCreateRequest, ApiKeyCreateResponse
from app.services.auth import create_api_key


router = APIRouter(prefix="/api/actors", tags=["actors"])


@router.get("", response_model=list[ActorRead])
def api_list_actors(session: DbSession) -> list[ActorRead]:
    return list(session.scalars(select(Actor).order_by(Actor.created_at.desc())).all())


@router.post("/api-keys", response_model=ApiKeyCreateResponse)
def api_create_actor_api_key(payload: ApiKeyCreateRequest, session: DbSession) -> ApiKeyCreateResponse:
    actor, api_key, raw_key = create_api_key(
        session,
        actor_name=payload.actor_name,
        actor_type=payload.actor_type.value,
        label=payload.label,
    )
    return ApiKeyCreateResponse(
        actor=actor,
        api_key=raw_key,
        key_prefix=api_key.key_prefix,
        label=api_key.label,
        created_at=api_key.created_at,
    )


@router.get("/me", response_model=ActorRead)
def api_get_current_actor(actor: CurrentActor) -> ActorRead:
    return actor
