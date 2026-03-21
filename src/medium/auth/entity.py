import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime

from medium.users.types import UserId

from .constants import SESSION_BYTES
from .value_objects import SessionHash, SessionToken


@dataclass
class UserSession:
    session_hash: SessionHash
    user_id: UserId
    expires_at: datetime
    revoked_at: datetime | None = None


def generate_session_token() -> SessionToken:
    token = secrets.token_urlsafe(SESSION_BYTES)
    return SessionToken(token)


def hash_session_token(token: SessionToken) -> SessionHash:
    encoded = token.value.encode()
    session_hash = hashlib.sha256(encoded).hexdigest()
    return SessionHash(session_hash)
