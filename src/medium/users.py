from sqlmodel import Session, select

from medium.database import User, engine


def create_user(email: str, username: str, password_hash: str) -> User:
    with Session(engine) as db:
        user = User(
            email=email,
            username=username,
            password_hash=password_hash,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def get_user(user_id: int) -> User | None:
    with Session(engine) as db:
        statement = select(User).where(User.id == user_id).limit(1)
        user = db.exec(statement).first()
    return user


def get_user_by_email(email: str) -> User | None:
    with Session(engine) as db:
        statement = select(User).where(User.email == email).limit(1)
        user = db.exec(statement).first()
    return user


def get_user_by_username(username: str) -> User | None:
    with Session(engine) as db:
        statement = select(User).where(User.username == username).limit(1)
        user = db.exec(statement).first()
    return user
