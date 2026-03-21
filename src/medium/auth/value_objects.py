from dataclasses import dataclass


@dataclass(frozen=True)
class CsrfToken:
    value: str


@dataclass(frozen=True)
class RefreshHash:
    value: str


@dataclass(frozen=True)
class RefreshToken:
    value: str


@dataclass(frozen=True)
class SessionHash:
    value: str


@dataclass(frozen=True)
class SessionToken:
    value: str
