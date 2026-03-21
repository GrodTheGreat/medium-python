import pathlib
from datetime import timedelta
from typing import Annotated
from uuid import uuid4

import jwt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse

from medium.auth.value_objects import CsrfToken, RefreshToken, SessionToken
from medium.users.dependencies import get_user_repo
from medium.users.entity import NewUser
from medium.users.exceptions import EmailConflictException, UsernameConflictException
from medium.users.repository import UserRepository
from medium.users.schemas import UserSchema
from medium.users.value_objects import Email, RawPassword, Username
from medium.utils import now

from .constants import (
    ACCESS_AUDIENCE,
    ACCESS_ISSUER,
    ACCESS_SIGNING_KEY,
    CSRF_KEY,
    REFRESH_KEY,
    REFRESH_MAX_AGE,
    SESSION_KEY,
    SESSION_MAX_AGE,
)
from .dependencies import (
    csrf_service,
    get_csrf,
    get_identity_service,
    get_refresh_repo,
    get_session_repo,
    require_anon,
    require_auth,
    verify_csrf,
)
from .entity import (
    UserRefreshToken,
    UserSession,
    generate_refresh_token,
    generate_session_token,
    hash_refresh_token,
    hash_session_token,
)
from .exceptions import PasswordMismatchException
from .repository import RefreshTokenRepository, SessionRepository
from .schemas import AuthPayload, SignInPayload, SignUpPayload
from .services import CsrfService, IdentityService, PasswordService
from .types import SignInFormData, SignUpFormData
from .utils import set_csrf_cookie, set_refresh_token_cookie, set_session_cookie

BASE_DIR = pathlib.Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"

auth_router = APIRouter()
templates = Jinja2Templates(TEMPLATES_DIR)


@auth_router.get("/sign-in", dependencies=[Depends(require_anon)])
async def get_sign_in(
    request: Request,
    csrf: Annotated[CsrfToken, Depends(get_csrf)],
) -> HTMLResponse:
    context = {"csrf": csrf.value}
    response = templates.TemplateResponse(request, "sign-in.html", context)
    set_csrf_cookie(response, csrf)
    return response


@auth_router.post(
    "/sign-in",
    dependencies=[Depends(verify_csrf), Depends(require_anon)],
)
async def sign_in(
    data: SignInFormData,
    identity: Annotated[IdentityService, Depends(get_identity_service)],
    service: Annotated[CsrfService, Depends(csrf_service)],
    session_repo: Annotated[SessionRepository, Depends(get_session_repo)],
):
    email = Email(data.email.strip().lower())
    password = RawPassword(data.password)
    user = identity.verify(email=email, password=password)
    session_token = generate_session_token()
    session_hash = hash_session_token(session_token)
    session = UserSession(
        session_hash,
        user.id,
        expires_at=now() + timedelta(seconds=SESSION_MAX_AGE),
    )
    session_repo.add(session)
    csrf_token = service.generate_token()
    response = RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    set_session_cookie(response, session_token)
    set_csrf_cookie(response, csrf_token)
    return response


@auth_router.get("/sign-up", dependencies=[Depends(require_anon)])
async def get_sign_up(
    request: Request,
    csrf: Annotated[CsrfToken, Depends(get_csrf)],
) -> HTMLResponse:
    context = {"csrf": csrf.value}
    response = templates.TemplateResponse(request, "sign-up.html", context)
    set_csrf_cookie(response, csrf)
    return response


@auth_router.post(
    "/sign-up",
    dependencies=[Depends(verify_csrf), Depends(require_anon)],
)
async def sign_up(
    data: SignUpFormData,
    service: Annotated[CsrfService, Depends(csrf_service)],
    session_repo: Annotated[SessionRepository, Depends(get_session_repo)],
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
):
    if data.password != data.confirm:
        raise PasswordMismatchException()
    email = Email(data.email.strip().lower())
    username = Username(data.username.strip().lower())
    password = RawPassword(data.password)
    existing_user = user_repo.get(email=email)
    if existing_user:
        raise EmailConflictException()
    existing_user = user_repo.get(username=username)
    if existing_user:
        raise UsernameConflictException()
    passwords = PasswordService()
    password_hash = passwords.hash_password(password)
    new_user = NewUser(email=email, username=username, password_hash=password_hash)
    user = user_repo.add(new_user)
    session_token = generate_session_token()
    session_hash = hash_session_token(session_token)
    session = UserSession(
        session_hash,
        user.id,
        expires_at=now() + timedelta(seconds=SESSION_MAX_AGE),
    )
    session_repo.add(session)
    csrf_token = service.generate_token()
    response = RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    set_session_cookie(response, session_token)
    set_csrf_cookie(response, csrf_token)
    return response


@auth_router.get("/sign-out", dependencies=[Depends(require_auth)])
async def get_sign_out(
    request: Request,
    csrf: Annotated[CsrfToken, Depends(get_csrf)],
) -> HTMLResponse:
    context = {"csrf": csrf.value}
    response = templates.TemplateResponse(request, "sign-out.html", context)
    set_csrf_cookie(response, csrf)
    return response


@auth_router.post(
    "/sign-out",
    dependencies=[Depends(verify_csrf), Depends(require_auth)],
)
async def sign_out(
    session_cookie: Annotated[str, Cookie(alias=SESSION_KEY)],
    sessions: Annotated[SessionRepository, Depends(get_session_repo)],
) -> RedirectResponse:
    session_token = SessionToken(session_cookie)
    session_hash = hash_session_token(session_token)
    session = sessions.get(session_hash=session_hash)
    if session is not None:
        session.revoked_at = now()
        sessions.save(session)
    response = RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key=SESSION_KEY)
    response.delete_cookie(key=CSRF_KEY)
    return response


api_router = APIRouter()


@api_router.post("/auth/refresh")
async def api_refresh(
    response: Response,
    refresh_repo: Annotated[RefreshTokenRepository, Depends(get_refresh_repo)],
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
    refresh_cookie: Annotated[str | None, Cookie(alias=REFRESH_KEY)] = None,
) -> AuthPayload:
    if refresh_cookie is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    refresh_token = RefreshToken(refresh_cookie)
    refresh_hash = hash_refresh_token(refresh_token)
    user = user_repo.get(refresh_hash=refresh_hash)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    refresh = refresh_repo.get(token_hash=refresh_hash)
    if refresh is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    refresh.revoked_at = now()
    refresh_repo.save(refresh)
    current_timestamp = now()
    access = jwt.encode(
        {
            "exp": current_timestamp + timedelta(minutes=15),
            "iss": ACCESS_ISSUER,
            "aud": ACCESS_AUDIENCE,
            "iat": current_timestamp,
            "sub": user.id.value,
            "jti": str(uuid4()),
            "username": user.username.value,
        },
        ACCESS_SIGNING_KEY,
        algorithm="HS256",
    )
    refresh_token = generate_refresh_token()
    refresh_hash = hash_refresh_token(refresh_token)
    refresh = UserRefreshToken(
        token_hash=refresh_hash,
        user_id=user.id,
        expires_at=current_timestamp + timedelta(seconds=REFRESH_MAX_AGE),
    )
    refresh = refresh_repo.add(refresh)
    set_refresh_token_cookie(response, refresh_token)
    return AuthPayload(
        user=UserSchema(id=user.id.value, username=user.username.value),
        access=access,
    )


@api_router.post("/auth/sign-in")
async def api_sign_in(
    payload: SignInPayload,
    response: Response,
    identity: Annotated[IdentityService, Depends(get_identity_service)],
    refresh_repo: Annotated[RefreshTokenRepository, Depends(get_refresh_repo)],
) -> AuthPayload:
    email = Email(payload.email.strip().lower())
    password = RawPassword(payload.password)
    user = identity.verify(email=email, password=password)
    current_timestamp = now()
    access = jwt.encode(
        {
            "exp": current_timestamp + timedelta(minutes=15),
            "iss": ACCESS_ISSUER,
            "aud": ACCESS_AUDIENCE,
            "iat": current_timestamp,
            "sub": user.id.value,
            "jti": str(uuid4()),
            "username": user.username.value,
        },
        ACCESS_SIGNING_KEY,
        algorithm="HS256",
    )
    refresh_token = generate_refresh_token()
    refresh_hash = hash_refresh_token(refresh_token)
    refresh = UserRefreshToken(
        token_hash=refresh_hash,
        user_id=user.id,
        expires_at=current_timestamp + timedelta(seconds=REFRESH_MAX_AGE),
    )
    refresh = refresh_repo.add(refresh)
    set_refresh_token_cookie(response, refresh_token)
    return AuthPayload(
        user=UserSchema(id=user.id.value, username=user.username.value),
        access=access,
    )


@api_router.post("/auth/sign-out", dependencies=[Depends(require_auth)])
async def api_sign_out(
    response: Response,
    refresh_repo: Annotated[RefreshTokenRepository, Depends(get_refresh_repo)],
    refresh_cookie: Annotated[str | None, Cookie(alias=REFRESH_KEY)] = None,
):
    if refresh_cookie is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    refresh_token = RefreshToken(refresh_cookie)
    refresh_hash = hash_refresh_token(refresh_token)
    refresh = refresh_repo.get(token_hash=refresh_hash)
    if refresh is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    refresh.revoked_at = now()
    refresh_repo.save(refresh)
    response.delete_cookie(key=REFRESH_KEY, path="/api/auth/refresh")
    return response


@api_router.post("/auth/sign-up")
async def api_sign_up(
    payload: SignUpPayload,
    response: Response,
    refresh_repo: Annotated[RefreshTokenRepository, Depends(get_refresh_repo)],
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
) -> AuthPayload:
    if payload.password != payload.confirm:
        raise PasswordMismatchException()
    email = Email(payload.email.strip().lower())
    username = Username(payload.username.strip().lower())
    password = RawPassword(payload.password)
    existing_user = user_repo.get(email=email)
    if existing_user:
        raise EmailConflictException()
    existing_user = user_repo.get(username=username)
    if existing_user:
        raise UsernameConflictException()
    passwords = PasswordService()
    password_hash = passwords.hash_password(password)
    new_user = NewUser(email=email, username=username, password_hash=password_hash)
    user = user_repo.add(new_user)
    current_timestamp = now()
    access = jwt.encode(
        {
            "exp": current_timestamp + timedelta(minutes=15),
            "iss": ACCESS_ISSUER,
            "aud": ACCESS_AUDIENCE,
            "iat": current_timestamp,
            "sub": user.id.value,
            "jti": str(uuid4()),
            "username": user.username.value,
        },
        ACCESS_SIGNING_KEY,
        algorithm="HS256",
    )
    refresh_token = generate_refresh_token()
    refresh_hash = hash_refresh_token(refresh_token)
    refresh = UserRefreshToken(
        token_hash=refresh_hash,
        user_id=user.id,
        expires_at=current_timestamp + timedelta(seconds=REFRESH_MAX_AGE),
    )
    refresh = refresh_repo.add(refresh)
    set_refresh_token_cookie(response, refresh_token)
    return AuthPayload(
        user=UserSchema(id=user.id.value, username=user.username.value),
        access=access,
    )
