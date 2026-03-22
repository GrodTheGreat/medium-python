from datetime import datetime

from sqlmodel import Session, col, select

from medium.users.types import UserId

from .entity import UserRefreshToken, UserSession
from .records import RefreshTokenRecord, UserSessionRecord
from .value_objects import RefreshHash, SessionHash


class RefreshTokenRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, token: UserRefreshToken) -> UserRefreshToken:
        new_refresh_token = RefreshTokenRecord(
            token_hash=token.token_hash.value,
            user_id=token.user_id.value,
            expires_at=token.expires_at,
            revoked_at=token.revoked_at,
        )
        self._session.add(new_refresh_token)
        self._session.commit()
        self._session.refresh(new_refresh_token)
        return _refresh_token_record_to_entity(new_refresh_token)

    def get(
        self,
        *,
        token_hash: RefreshHash | None = None,
        user_id: UserId | None = None,
        expires_at: datetime | None = None,
        revoked_at: datetime | None = None,
    ) -> UserRefreshToken | None:
        statement = select(RefreshTokenRecord)
        if token_hash:
            statement = statement.where(
                RefreshTokenRecord.token_hash == token_hash.value
            )
        if user_id:
            statement = statement.where(RefreshTokenRecord.user_id == user_id.value)
        if expires_at:
            statement = statement.where(RefreshTokenRecord.expires_at > expires_at)
        statement = statement.where(col(RefreshTokenRecord.revoked_at).is_(revoked_at))
        refresh_token = self._session.exec(statement).first()
        if refresh_token is None:
            return None
        return _refresh_token_record_to_entity(refresh_token)

    def save(self, token: UserRefreshToken) -> UserRefreshToken:
        statement = (
            select(RefreshTokenRecord)
            .where(
                RefreshTokenRecord.token_hash == token.token_hash.value,
                RefreshTokenRecord.user_id == token.user_id.value,
            )
            .limit(1)
        )
        refresh_token = self._session.exec(statement).first()
        if refresh_token is None:
            raise Exception()
        refresh_token.expires_at = token.expires_at
        refresh_token.revoked_at = token.revoked_at
        self._session.commit()
        self._session.refresh(refresh_token)
        return _refresh_token_record_to_entity(refresh_token)


def _refresh_token_record_to_entity(token: RefreshTokenRecord) -> UserRefreshToken:
    if token.user_id is None:
        # TODO: this shouldn't really be possible, but it would signal something went wrong with the db or sqlmodel
        raise Exception()
    return UserRefreshToken(
        token_hash=RefreshHash(token.token_hash),
        user_id=UserId(token.user_id),
        expires_at=token.expires_at,
        revoked_at=token.revoked_at,
    )


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
        return _session_record_to_entity(new_session)

    def get(
        self,
        *,
        session_hash: SessionHash | None = None,
        user_id: UserId | None = None,
        expires_at: datetime | None = None,
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
        return _session_record_to_entity(session)

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
        return _session_record_to_entity(session_record)


def _session_record_to_entity(session: UserSessionRecord) -> UserSession:
    if session.user_id is None:
        # TODO: this shouldn't really be possible, but it would signal something went wrong with the db or sqlmodel
        raise Exception()
    return UserSession(
        session_hash=SessionHash(session.session_hash),
        user_id=UserId(session.user_id),
        expires_at=session.expires_at,
        revoked_at=session.revoked_at,
    )
