from datetime import datetime, timezone

from sqlmodel import Session, col, select

from ..users.types import UserId
from .entity import UserSession
from .records import UserSessionRecord
from .value_objects import SessionHash


class SessionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, session: UserSession) -> UserSession:
        new_session = UserSessionRecord(
            session_hash=session.session_hash.value,
            user_id=session.user_id.value,
            expires_at=session.expires_at,
        )
        self._session.add(new_session)
        self._session.commit()
        self._session.refresh(new_session)
        return session_record_to_entity(new_session)

    def get(
        self,
        *,
        session_hash: SessionHash | None = None,
        user_id: UserId | None = None,
        expires_at: datetime | None = datetime.now(timezone.utc),
        revoked_at: datetime | None = None,
    ) -> UserSession | None:
        statement = select(UserSessionRecord)
        if session_hash:
            statement = statement.where(
                UserSessionRecord.session_hash == session_hash.value
            )
        if user_id:
            statement = statement.where(UserSessionRecord.user_id == user_id.value)
        if expires_at:
            statement = statement.where(UserSessionRecord.expires_at > expires_at)
        statement = statement.where(
            col(UserSessionRecord.revoked_at).is_(revoked_at)
        ).limit(1)
        session = self._session.exec(statement).first()
        if session is None:
            return None
        return session_record_to_entity(session)

    def save(self, session: UserSession) -> UserSession:
        statement = (
            select(UserSessionRecord)
            .where(
                UserSessionRecord.session_hash == session.session_hash.value,
                UserSessionRecord.user_id == session.user_id.value,
            )
            .limit(1)
        )
        session_record = self._session.exec(statement).first()
        if session_record is None:
            raise Exception()
        session_record.expires_at = session.expires_at
        session_record.revoked_at = session.revoked_at
        self._session.commit()
        self._session.refresh(session_record)
        return session_record_to_entity(session_record)


def session_record_to_entity(session: UserSessionRecord) -> UserSession:
    return UserSession(
        session_hash=SessionHash(session.session_hash),
        user_id=UserId(session.user_id),
        expires_at=session.expires_at,
        revoked_at=session.revoked_at,
    )
