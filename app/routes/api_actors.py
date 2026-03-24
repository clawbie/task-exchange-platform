from fastapi import APIRouter
from sqlalchemy import select

from app.deps import DbSession
from app.models.actor import Actor
from app.schemas.actor import ActorRead


router = APIRouter(prefix="/api/actors", tags=["actors"])


@router.get("", response_model=list[ActorRead])
def api_list_actors(session: DbSession) -> list[ActorRead]:
    return list(session.scalars(select(Actor).order_by(Actor.created_at.desc())).all())
