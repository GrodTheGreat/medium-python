from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from sqlmodel import Session

from medium.auth.entity import CurrentUser
from medium.dependencies import get_db
from medium.users.dependencies import get_user_repo
from medium.users.entity import User
from medium.users.repository import UserRepository

from .constants import (
    CSRF_KEY,
    CSRF_SIGNING_KEY,
    SESSION_KEY,
    XSRF_INPUT,
    XSRF_KEY,
)
from .repository import RefreshTokenRepository, SessionRepository
from .services import (
    CsrfService,
    IdentityService,
    PasswordService,
    SessionService,
    decode_access_token,
)
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


def get_current_user(
    request: Request,
    sessions: Annotated[SessionService, Depends(get_session_service)],
    users: Annotated[UserRepository, Depends(get_user_repo)],
) -> CurrentUser | None:
    access_token = request.headers.get("Authorization")
    if access_token:
        token = access_token.removeprefix("Bearer ")
        return decode_access_token(token)
    session_token = request.cookies.get(SESSION_KEY)
    if session_token is None:
        return None
    session_hash = sessions.hash_token(SessionToken(session_token))
    user = users.get(session_hash=session_hash)
    if user is None:
        return None
    return CurrentUser(id=user.id, username=user.username)


def require_anon(user: Annotated[User | None, Depends(get_current_user)]) -> None:
    if user is not None:
        print("not anon")
        # TODO: There is almost certainly a better response here
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)


def require_auth(user: Annotated[User | None, Depends(get_current_user)]) -> None:
    if user is None:
        print("not auth")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
