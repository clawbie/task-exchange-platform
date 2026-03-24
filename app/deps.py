from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_session
from app.models.actor import Actor
from app.services.auth import authenticate_api_key


DbSession = Annotated[Session, Depends(get_session)]


def get_current_actor(
    session: DbSession,
    authorization: str | None = Header(default=None),
) -> Actor:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header")

    actor = authenticate_api_key(session, token)
    if not actor:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    return actor


CurrentActor = Annotated[Actor, Depends(get_current_actor)]
