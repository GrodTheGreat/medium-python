from typing import Generator

from sqlmodel import Session

from medium.database import engine


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
