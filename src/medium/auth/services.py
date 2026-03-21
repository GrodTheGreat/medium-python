import hashlib
import hmac
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from medium.auth.exceptions import InvalidCredentialsException
from medium.users.entity import NewUser, User
from medium.users.exceptions import EmailConflictException, UsernameConflictException
from medium.users.repository import UserRepository
from medium.users.value_objects import Email, HashedPassword, RawPassword, Username

from .constants import CSRF_BYTES, SEPARATOR
from .value_objects import CsrfToken


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
