from dataclasses import dataclass


@dataclass(frozen=True)
class CsrfToken:
    value: str


@dataclass(frozen=True)
class SessionToken:
    value: str


@dataclass(frozen=True)
class SessionHash:
    value: str
