from dataclasses import dataclass

from .types import UserId
from .value_objects import Email, HashedPassword, Username


@dataclass(frozen=True)
class NewUser:
    email: Email
    username: Username
    password_hash: HashedPassword


@dataclass
class User:
    id: UserId
    email: Email
    username: Username
    password_hash: HashedPassword
