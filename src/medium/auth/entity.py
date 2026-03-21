import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime

from medium.users.types import UserId

from .constants import REFRESH_BYTES
from .value_objects import RefreshHash, RefreshToken, SessionHash


@dataclass
class UserRefreshToken:
    token_hash: RefreshHash
    user_id: UserId
    expires_at: datetime
    revoked_at: datetime | None = None


def generate_refresh_token() -> RefreshToken:
    token = secrets.token_urlsafe(REFRESH_BYTES)
    return RefreshToken(token)


def hash_refresh_token(token: RefreshToken) -> RefreshHash:
    encoded = token.value.encode()
    refresh_hash = hashlib.sha256(encoded).hexdigest()
    return RefreshHash(refresh_hash)


@dataclass
class UserSession:
    session_hash: SessionHash
    user_id: UserId
    expires_at: datetime
    revoked_at: datetime | None = None
