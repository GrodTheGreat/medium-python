import hashlib
import hmac
import json
import pathlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Form, Path, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from medium.database import Article, ArticleStatus, User, UserSession, engine
from medium.exceptions import NotFoundException
from medium.passwords import hash_password, is_correct_password
from medium.schemas import BaseSchema
from medium.users import create_user, get_user_by_email, get_user_by_username

BASE_DIR = pathlib.Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"

templates = Jinja2Templates(TEMPLATES_DIR)

ArticleIdRouteParam = Annotated[int, Path(alias="articleId", ge=1)]

ssr = APIRouter()


class SignInFormData(BaseSchema):
    email: str
    password: str


class SignUpFormData(BaseSchema):
    email: str
    username: str
    password: str
    confirm: str


SESSION_TOKEN_KEY = "Medium-Session-Token"

SessionCookie = Annotated[str | None, Cookie(alias=SESSION_TOKEN_KEY)]
SignInForm = Annotated[SignInFormData, Form()]
SignUpForm = Annotated[SignUpFormData, Form()]


def require_anon(session: SessionCookie) -> None:
    if not session:
        return
    # TODO: Look up user by (valid) session, if found then throw


@ssr.get("/", status_code=status.HTTP_200_OK)
async def get_index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@ssr.get(
    "/sign-in",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_anon)],
)
async def get_sign_in(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "sign-in.html")


@ssr.post(
    "/sign-in",
    # TODO: Should status code be 302?
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_anon)],
)
async def sign_in(data: SignInForm):
    email = data.email.strip().lower()
    user = get_user_by_email(email)
    if user is None or not is_correct_password(data.password, user.password_hash):
        raise Exception()
    with Session(engine) as db:
        session_token = secrets.token_urlsafe(64)
        session_hash = hashlib.sha256(session_token.encode()).hexdigest()
        max_age = 60 * 5
        expiry = datetime.now(timezone.utc) + timedelta(seconds=max_age)
        session = UserSession(
            session_hash=session_hash,
            user_id=user.id,  # type: ignore
            expires_at=expiry,
        )
        db.add(session)
        db.commit()
    csrf_token = secrets.token_urlsafe(32)
    signature = hmac.new(
        "super-secret-key".encode(),
        csrf_token.encode(),
        hashlib.sha256,
    )
    csrf = f"{csrf_token}.{signature}"
    redirect = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    redirect.set_cookie(
        key=SESSION_TOKEN_KEY,
        value=session_token,
        max_age=max_age,
        secure=False,
        httponly=True,
    )
    redirect.set_cookie(
        key="Medium-CSRF-Token",
        value=csrf,
        max_age=max_age,
        secure=False,
    )
    return redirect


@ssr.get("/sign-out", status_code=status.HTTP_200_OK)
async def get_sign_out(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "sign-out.html")


@ssr.post("/sign-out")
async def sign_out():
    pass


@ssr.get(
    "/sign-up",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_anon)],
)
async def get_sign_up(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "sign-up.html")


@ssr.post("/sign-up", dependencies=[Depends(require_anon)])
async def sign_up(data: SignUpForm):
    if data.password != data.confirm:
        raise Exception()
    email = data.email.strip().lower()
    existing_user = get_user_by_email(email)
    if existing_user is not None:
        raise Exception()
    username = data.username.strip()
    existing_user = get_user_by_username(username)
    if existing_user is not None:
        raise Exception()
    user = create_user(email, username, hash_password(data.password))
    with Session(engine) as db:
        session_token = secrets.token_urlsafe(64)
        session_hash = hashlib.sha256(session_token.encode()).hexdigest()
        max_age = 60 * 5
        expiry = datetime.now(timezone.utc) + timedelta(seconds=max_age)
        session = UserSession(
            session_hash=session_hash,
            user_id=user.id,  # type: ignore
            expires_at=expiry,
        )
        db.add(session)
        db.commit()
    csrf_token = secrets.token_urlsafe(32)
    signature = hmac.new(
        "super-secret-key".encode(),
        csrf_token.encode(),
        hashlib.sha256,
    )
    csrf = f"{csrf_token}.{signature}"
    redirect = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    redirect.set_cookie(
        key=SESSION_TOKEN_KEY,
        value=session_token,
        max_age=max_age,
        secure=False,
        httponly=True,
    )
    redirect.set_cookie(
        key="Medium-CSRF-Token",
        value=csrf,
        max_age=max_age,
        secure=False,
    )
    return redirect


@ssr.get("/new-story", status_code=status.HTTP_200_OK)
async def get_new_story(request: Request):
    return templates.TemplateResponse(request, "editor.html", {"article_content": None})


@ssr.get("/p/{articleId:int}/edit", status_code=status.HTTP_200_OK)
async def get_edit_article(request: Request, article_id: ArticleIdRouteParam):
    with Session(engine) as db:
        statement = select(Article).where(Article.id == article_id).limit(1)
        article = db.exec(statement).first()
        if article is None:
            raise NotFoundException()
        if article.id is None:
            raise Exception()

    return templates.TemplateResponse(
        request,
        "editor.html",
        {
            "article_content": json.loads(article.json_content)
            if article.json_content
            else None
        },
    )


@ssr.get("/{namespace:str}/{slug:str}-{articleId:int}", status_code=status.HTTP_200_OK)
async def get_published_article(
    request: Request,
    namespace: str,
    slug: str,
    article_id: ArticleIdRouteParam,
):
    with Session(engine) as db:
        statement = (
            select(Article)
            .where(Article.id == article_id, Article.status == ArticleStatus.PUBLISHED)
            .limit(1)
        )
        article = db.exec(statement).first()
    if article is None:
        return templates.TemplateResponse(request, "404.html")
    with Session(engine) as db:
        statement = select(User).where(User.id == article.author_id).limit(1)
        author = db.exec(statement).first()
    if author is None:
        raise Exception()
    if author.username != namespace or article.slug != slug:
        return RedirectResponse(
            f"/{author.username}/{article.slug}-{article.id}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    return templates.TemplateResponse(
        request,
        "article.html",
        {"title": article.title, "article_content": article.html_content},
    )
