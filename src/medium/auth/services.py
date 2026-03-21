import hashlib
import hmac
import secrets
from datetime import timedelta
from uuid import uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from medium.users.entity import NewUser, User
from medium.users.exceptions import EmailConflictException, UsernameConflictException
from medium.users.repository import UserRepository
from medium.users.types import UserId
from medium.users.value_objects import Email, HashedPassword, RawPassword, Username
from medium.utils import now

from .constants import (
    ACCESS_AUDIENCE,
    ACCESS_ISSUER,
    ACCESS_SIGNING_KEY,
    CSRF_BYTES,
    SEPARATOR,
    SESSION_BYTES,
    SESSION_MAX_AGE,
)
from .entity import CurrentUser, UserSession
from .exceptions import InvalidCredentialsException
from .repository import SessionRepository
from .value_objects import CsrfToken, SessionHash, SessionToken


def create_access_token(user: User) -> str:
    current_timestamp = now()
    return jwt.encode(
        {
            "exp": current_timestamp + timedelta(minutes=15),
            "iss": ACCESS_ISSUER,
            "aud": ACCESS_AUDIENCE,
            "iat": current_timestamp,
            "sub": user.id.value,
            "jti": str(uuid4()),
            "username": user.username.value,
        },
        ACCESS_SIGNING_KEY,
        algorithm="HS256",
    )


def decode_access_token(token: str) -> CurrentUser | None:
    try:
        payload = jwt.decode(
            token,
            key=ACCESS_SIGNING_KEY,
            algorithms=["HS256"],
            issuer=ACCESS_ISSUER,
            audience=ACCESS_AUDIENCE,
        )
    except jwt.PyJWTError:
        return None
    user_id = payload.get("sub")
    username = payload.get("username")
    if user_id is None or username is None:
        raise Exception()
    return CurrentUser(id=UserId(user_id), username=Username(username))


class CsrfService:
    def __init__(self, key: str) -> None:
        self._algorithm = hashlib.sha256
        self._key: bytes = key.encode()

    def generate_token(self) -> CsrfToken:
        payload = secrets.token_urlsafe(CSRF_BYTES)
        signature = self._generate_signature(payload)
        return CsrfToken(f"{payload}{SEPARATOR}{signature}")

    def _generate_signature(self, payload: str) -> str:
        return hmac.new(
            self._key,
            payload.encode(),
            self._algorithm,
        ).hexdigest()

    def validate_csrf(self, token: CsrfToken) -> bool:
        try:
            payload, signature = token.value.rsplit(SEPARATOR, maxsplit=1)
        except ValueError:
            return False
        expected = self._generate_signature(payload)
        return hmac.compare_digest(signature, expected)


class PasswordService:
    def __init__(self):
        self._hasher = PasswordHasher()

    def hash_password(self, password: RawPassword) -> HashedPassword:
        password_hash = self._hasher.hash(password.value)
        return HashedPassword(password_hash)

    def is_correct_password(
        self,
        password: RawPassword,
        hashed_password: HashedPassword,
    ) -> bool:
        try:
            return self._hasher.verify(hashed_password.value, password.value)
        except (InvalidHashError, VerificationError, VerifyMismatchError):
            return False


class SessionService:
    def __init__(self, session_repo: SessionRepository) -> None:
        self._session_repo = session_repo

    # TODO: kinda want a better name for this...
    def create(self, user: User) -> SessionToken:
        token = self._generate_token()
        token_hash = self.hash_token(token)
        session = UserSession(
            token_hash,
            user.id,
            expires_at=now() + timedelta(seconds=SESSION_MAX_AGE),
        )
        self._session_repo.add(session)
        return token

    def revoke(self, token: SessionToken) -> None:
        token_hash = self.hash_token(token)
        session = self._session_repo.get(session_hash=token_hash)
        if session is not None:
            session.revoked_at = now()
            self._session_repo.save(session)

    # TODO: I am not thrilled with the static methods here, these should
    # arguably be standard functions outside the class
    @staticmethod
    def hash_token(token: SessionToken) -> SessionHash:
        encoded = token.value.encode()
        session_hash = hashlib.sha256(encoded).hexdigest()
        return SessionHash(session_hash)

    @staticmethod
    def _generate_token() -> SessionToken:
        token = secrets.token_urlsafe(SESSION_BYTES)
        return SessionToken(token)


class IdentityService:
    def __init__(self, passwords: PasswordService, users: UserRepository) -> None:
        self._passwords = passwords
        self._users = users

    def verify(self, email: Email, password: RawPassword) -> User:
        user = self._users.get(email=email)
        if user is None or not self._passwords.is_correct_password(
            password=password,
            hashed_password=user.password_hash,
        ):
            raise InvalidCredentialsException()
        return user

    def register(self, email: Email, username: Username, password: RawPassword) -> User:
        existing_user = self._users.get(email=email)
        if existing_user:
            raise EmailConflictException()
        existing_user = self._users.get(username=username)
        if existing_user:
            raise UsernameConflictException()
        password_hash = self._passwords.hash_password(password)
        new_user = NewUser(email=email, username=username, password_hash=password_hash)
        return self._users.add(new_user)
