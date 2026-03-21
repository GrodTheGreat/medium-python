from typing import Annotated

import jwt
from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from sqlmodel import Session

from medium.dependencies import get_db
from medium.users.dependencies import get_user_repo
from medium.users.entity import User
from medium.users.repository import UserRepository
from medium.users.types import UserId

from .constants import (
    ACCESS_AUDIENCE,
    ACCESS_ISSUER,
    ACCESS_SIGNING_KEY,
    CSRF_KEY,
    CSRF_SIGNING_KEY,
    SESSION_KEY,
    XSRF_INPUT,
    XSRF_KEY,
)
from .repository import RefreshTokenRepository, SessionRepository
from .services import CsrfService, IdentityService, PasswordService, SessionService
from .value_objects import CsrfToken, SessionToken


def get_refresh_repo(db: Annotated[Session, Depends(get_db)]) -> RefreshTokenRepository:
    return RefreshTokenRepository(db)


def get_session_repo(db: Annotated[Session, Depends(get_db)]) -> SessionRepository:
    return SessionRepository(db)


def csrf_service() -> CsrfService:
    return CsrfService(CSRF_SIGNING_KEY)


def get_session_service(
    repo: Annotated[SessionRepository, Depends(get_session_repo)],
) -> SessionService:
    return SessionService(session_repo=repo)


def get_identity_service(
    users: Annotated[UserRepository, Depends(get_user_repo)],
) -> IdentityService:
    return IdentityService(passwords=PasswordService(), users=users)


def get_csrf(
    csrf: Annotated[CsrfService, Depends(csrf_service)],
    csrf_cookie: Annotated[str | None, Cookie(alias=CSRF_KEY)] = None,
) -> CsrfToken:
    if csrf_cookie is not None:
        return CsrfToken(csrf_cookie)
    return csrf.generate_token()


async def verify_csrf(
    request: Request,
    service: Annotated[CsrfService, Depends(csrf_service)],
    csrf_cookie: Annotated[str | None, Cookie(alias=CSRF_KEY)] = None,
    xsrf_header: Annotated[str | None, Header(alias=XSRF_KEY)] = None,
) -> None:
    # TODO: I have no idea what the correct response for these cases is
    if not csrf_cookie:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    xsrf = xsrf_header
    if xsrf is None:
        form = await request.form()
        xsrf = form.get(XSRF_INPUT)
    if not xsrf:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    if csrf_cookie != xsrf:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    csrf = CsrfToken(csrf_cookie)
    if not service.validate_csrf(csrf):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


# TODO: Would probably be better to have a simplified "CurrentUser" object that
# unifies auth methods instead of returning a User object
def get_current_user(
    request: Request,
    sessions: Annotated[SessionService, Depends(get_session_service)],
    users: Annotated[UserRepository, Depends(get_user_repo)],
) -> User | None:
    access_token = request.headers.get("Authorization")
    if access_token:
        token = access_token.removeprefix("Bearer ")
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
        user_id: int | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        # TODO: This is dumb because the point of the access token is we don't need a db hit, but I am keeping it for now
        return users.get(user_id=UserId(user_id))
    session_token = request.cookies.get(SESSION_KEY)
    if session_token is None:
        return None
    session_hash = sessions.hash_token(SessionToken(session_token))
    return users.get(session_hash=session_hash)


def require_anon(user: Annotated[User | None, Depends(get_current_user)]) -> None:
    if user is not None:
        print("not anon")
        # TODO: There is almost certainly a better response here
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)


def require_auth(user: Annotated[User | None, Depends(get_current_user)]) -> None:
    if user is None:
        print("not auth")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
