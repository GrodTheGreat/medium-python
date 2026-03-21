from fastapi import Response

from ..constants import IS_PROD
from .constants import (
    CSRF_KEY,
    CSRF_MAX_AGE,
    REFRESH_KEY,
    REFRESH_MAX_AGE,
    SESSION_KEY,
    SESSION_MAX_AGE,
)
from .value_objects import CsrfToken, RefreshToken, SessionToken


def set_csrf_cookie(response: Response, token: CsrfToken) -> None:
    response.set_cookie(
        key=CSRF_KEY,
        value=token.value,
        max_age=CSRF_MAX_AGE,
        secure=IS_PROD,
        httponly=False,
    )


def set_refresh_token_cookie(response: Response, token: RefreshToken) -> None:
    response.set_cookie(
        key=REFRESH_KEY,
        value=token.value,
        max_age=REFRESH_MAX_AGE,
        path="/api/auth/refresh",
        secure=IS_PROD,
        httponly=True,
    )


def set_session_cookie(response: Response, token: SessionToken) -> None:
    response.set_cookie(
        key=SESSION_KEY,
        value=token.value,
        max_age=SESSION_MAX_AGE,
        secure=IS_PROD,
        httponly=True,
    )
