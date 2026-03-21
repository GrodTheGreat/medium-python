from sqlmodel import Session, SQLModel, StaticPool, create_engine

from medium.auth.records import RefreshTokenRecord, UserSessionRecord
from medium.auth.services import PasswordService
from medium.users.record import UserRecord
from medium.users.value_objects import RawPassword

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    echo=True,
    poolclass=StaticPool,
)
SQLModel.metadata.create_all(
    engine,
    tables=[
        RefreshTokenRecord.__table__,
        UserRecord.__table__,
        UserSessionRecord.__table__,
    ],
)
hasher = PasswordService()
with Session(engine) as session:
    u1 = UserRecord(
        email="user@email.com",
        username="user1",
        password_hash=hasher.hash_password(RawPassword("password")).value,
    )
    session.add(u1)
    session.commit()
