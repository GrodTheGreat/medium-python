from sqlmodel import Session, col, select

from medium.auth.records import RefreshTokenRecord, UserSessionRecord
from medium.auth.value_objects import RefreshHash, SessionHash
from medium.utils import now

from .entity import NewUser, User
from .record import UserRecord
from .types import UserId
from .value_objects import Email, HashedPassword, Username


class UserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, user: NewUser) -> User:
        new_user = UserRecord(
            email=user.email.value,
            username=user.username.value,
            password_hash=user.password_hash.value,
        )
        self._session.add(new_user)
        self._session.commit()
        self._session.refresh(new_user)
        return user_record_to_entity(new_user)

    def get(
        self,
        *,
        user_id: UserId | None = None,
        email: Email | None = None,
        username: Username | None = None,
        refresh_hash: RefreshHash | None = None,
        session_hash: SessionHash | None = None,
    ) -> User | None:
        statement = select(UserRecord)
        if session_hash:
            statement = statement.join(UserSessionRecord).where(
                UserSessionRecord.session_hash == session_hash.value,
                UserSessionRecord.expires_at > now(),
                col(UserSessionRecord.revoked_at).is_(None),
            )
        if refresh_hash:
            statement = statement.join(RefreshTokenRecord).where(
                RefreshTokenRecord.token_hash == refresh_hash.value,
                RefreshTokenRecord.expires_at > now(),
                col(RefreshTokenRecord.revoked_at).is_(None),
            )
        if user_id:
            statement = statement.where(UserRecord.id == user_id.value)
        if email:
            statement = statement.where(UserRecord.email == email.value)
        if username:
            statement = statement.where(UserRecord.username == username.value)
        statement = statement.limit(1)
        user = self._session.exec(statement).first()
        if user is None:
            return None
        return user_record_to_entity(user)


def user_record_to_entity(user: UserRecord) -> User:
    return User(
        id=UserId(user.id),
        email=Email(user.email),
        username=Username(user.username),
        password_hash=HashedPassword(user.password_hash),
    )
