from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from medium.dependencies import get_db
from medium.users.repository import UserRepository


def get_user_repo(db: Annotated[Session, Depends(get_db)]) -> UserRepository:
    return UserRepository(db)
