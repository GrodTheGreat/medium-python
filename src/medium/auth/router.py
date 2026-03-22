import pathlib
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse

from medium.users.dependencies import get_user_repo
from medium.users.repository import UserRepository
from medium.users.schemas import UserSchema
from medium.users.value_objects import Email, RawPassword, Username

from .constants import (
    CSRF_KEY,
    REFRESH_KEY,
    SESSION_KEY,
)
from .dependencies import (
    csrf_service,
    get_csrf,
    get_identity_service,
    get_refresh_service,
    get_session_service,
    require_anon,
    require_auth,
    verify_csrf,
)
from .exceptions import PasswordMismatchException
from .schemas import AuthPayload, SignInPayload, SignUpPayload
from .services import (
    CsrfService,
    IdentityService,
    RefreshTokenService,
    SessionService,
    create_access_token,
    hash_refresh_token,
)
from .types import SignInFormData, SignUpFormData
from .utils import set_csrf_cookie, set_refresh_token_cookie, set_session_cookie
from .value_objects import CsrfToken, RefreshToken, SessionToken

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
    sessions: Annotated[SessionService, Depends(get_session_service)],
):
    email = Email(data.email.strip().lower())
    password = RawPassword(data.password)
    user = identity.verify(email=email, password=password)
    session_token = sessions.issue(user)
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
    sessions: Annotated[SessionService, Depends(get_session_service)],
) -> RedirectResponse:
    session_token = SessionToken(session_cookie)
    sessions.revoke(session_token)
    response = RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key=SESSION_KEY)
    response.delete_cookie(key=CSRF_KEY)
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
    identity: Annotated[IdentityService, Depends(get_identity_service)],
    service: Annotated[CsrfService, Depends(csrf_service)],
    sessions: Annotated[SessionService, Depends(get_session_service)],
):
    if data.password != data.confirm:
        raise PasswordMismatchException()
    email = Email(data.email.strip().lower())
    username = Username(data.username.strip().lower())
    password = RawPassword(data.password)
    user = identity.register(email=email, username=username, password=password)
    session_token = sessions.issue(user)
    csrf_token = service.generate_token()
    response = RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    set_session_cookie(response, session_token)
    set_csrf_cookie(response, csrf_token)
    return response


api_router = APIRouter()


@api_router.post("/auth/refresh")
async def api_refresh(
    response: Response,
    refresh_service: Annotated[RefreshTokenService, Depends(get_refresh_service)],
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
    refresh_service.revoke(refresh_hash)
    access = create_access_token(user)
    refresh_token = refresh_service.issue(user)
    set_refresh_token_cookie(response, refresh_token)
    return AuthPayload(
        user=UserSchema(id=user.id.value, username=user.username.value),
        access=access,
    )


@api_router.post("/auth/sign-in", dependencies=[Depends(require_anon)])
async def api_sign_in(
    payload: SignInPayload,
    response: Response,
    identity: Annotated[IdentityService, Depends(get_identity_service)],
    refresh_service: Annotated[RefreshTokenService, Depends(get_refresh_service)],
) -> AuthPayload:
    email = Email(payload.email.strip().lower())
    password = RawPassword(payload.password)
    user = identity.verify(email=email, password=password)
    access = create_access_token(user)
    refresh_token = refresh_service.issue(user)
    set_refresh_token_cookie(response, refresh_token)
    return AuthPayload(
        user=UserSchema(id=user.id.value, username=user.username.value),
        access=access,
    )


@api_router.post("/auth/sign-out", dependencies=[Depends(require_auth)])
async def api_sign_out(
    response: Response,
    refresh_service: Annotated[RefreshTokenService, Depends(get_refresh_service)],
    refresh_cookie: Annotated[str | None, Cookie(alias=REFRESH_KEY)] = None,
):
    if refresh_cookie is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    refresh_token = RefreshToken(refresh_cookie)
    refresh_hash = hash_refresh_token(refresh_token)
    refresh_service.revoke(refresh_hash)
    response.delete_cookie(key=REFRESH_KEY, path="/api/auth/refresh")
    return response


@api_router.post("/auth/sign-up", dependencies=[Depends(require_anon)])
async def api_sign_up(
    payload: SignUpPayload,
    response: Response,
    identity: Annotated[IdentityService, Depends(get_identity_service)],
    refresh_service: Annotated[RefreshTokenService, Depends(get_refresh_service)],
) -> AuthPayload:
    if payload.password != payload.confirm:
        raise PasswordMismatchException()
    email = Email(payload.email.strip().lower())
    username = Username(payload.username.strip().lower())
    password = RawPassword(payload.password)
    user = identity.register(email=email, username=username, password=password)
    access = create_access_token(user)
    refresh_token = refresh_service.issue(user)
    set_refresh_token_cookie(response, refresh_token)
    return AuthPayload(
        user=UserSchema(id=user.id.value, username=user.username.value),
        access=access,
    )
