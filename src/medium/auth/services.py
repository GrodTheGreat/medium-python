import hashlib
import hmac
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from medium.users.value_objects import HashedPassword, RawPassword

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
