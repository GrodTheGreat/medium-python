from dataclasses import dataclass
from datetime import datetime

from medium.users.types import UserId
from medium.users.value_objects import Username

from .value_objects import RefreshHash, SessionHash


@dataclass(frozen=True)
class CurrentUser:
    id: UserId
    username: Username


@dataclass
class UserRefreshToken:
    token_hash: RefreshHash
    user_id: UserId
    expires_at: datetime
    revoked_at: datetime | None = None


@dataclass
class UserSession:
    session_hash: SessionHash
    user_id: UserId
    expires_at: datetime
    revoked_at: datetime | None = None
