from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from sqlmodel import Session

from medium.auth.entity import hash_session_token
from medium.dependencies import get_db
from medium.users.dependencies import get_user_repo
from medium.users.entity import User
from medium.users.repository import UserRepository

from .constants import CSRF_KEY, CSRF_SIGNING_KEY, SESSION_KEY, XSRF_INPUT, XSRF_KEY
from .repository import SessionRepository
from .services import CsrfService
from .value_objects import CsrfToken, SessionToken


def get_session_repo(db: Annotated[Session, Depends(get_db)]) -> SessionRepository:
    return SessionRepository(db)


def csrf_service() -> CsrfService:
    return CsrfService(CSRF_SIGNING_KEY)


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
        print("no cookie")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    xsrf = xsrf_header
    if xsrf is None:
        form = await request.form()
        xsrf = form.get(XSRF_INPUT)
    if not xsrf:
        print("no xsrf")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    if csrf_cookie != xsrf:
        print("no match")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    csrf = CsrfToken(csrf_cookie)
    if not service.validate_csrf(csrf):
        print("not valid")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


def get_current_user(
    request: Request,
    users: Annotated[UserRepository, Depends(get_user_repo)],
) -> User | None:
    session_token = request.cookies.get(SESSION_KEY)
    if session_token is None:
        return None
    session_hash = hash_session_token(SessionToken(session_token))
    return users.get(session_hash=session_hash)


def require_anon(user: Annotated[User | None, Depends(get_current_user)]) -> None:
    if user is not None:
        print("not anon")
        # There is almost certainly a better response here
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)


def require_auth(user: Annotated[User | None, Depends(get_current_user)]) -> None:
    if user is None:
        print("not auth")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
