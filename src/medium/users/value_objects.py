from dataclasses import dataclass

from .exceptions import EmailValidationException, UsernameValidationException


@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        length = len(self.value)
        if length < 6:
            raise EmailValidationException("email too short")
        if length > 256:
            raise EmailValidationException("email too long")


@dataclass(frozen=True)
class Username:
    value: str

    def __post_init__(self) -> None:
        length = len(self.value)
        if length < 3:
            raise UsernameValidationException("username too short")
        if length > 50:
            raise UsernameValidationException("username too long")


@dataclass(frozen=True)
class RawPassword:
    value: str

    # TODO: Shouldn't necessarily check length or character, just entropy
    def __post_init__(self) -> None:
        length = len(self.value)


@dataclass(frozen=True)
class HashedPassword:
    value: str

    def __post_init__(self) -> None:
        # TODO: Should I do anything for this?
        pass
