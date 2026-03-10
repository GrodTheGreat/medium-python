import json
import pathlib
from typing import Annotated

from fastapi import APIRouter, Path, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from medium.database import Article, ArticleStatus, User, engine
from medium.exceptions import NotFoundException

BASE_DIR = pathlib.Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"

templates = Jinja2Templates(TEMPLATES_DIR)

ArticleIdRouteParam = Annotated[int, Path(alias="articleId", ge=1)]

ssr = APIRouter()


@ssr.get("/", status_code=status.HTTP_200_OK)
async def get_index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@ssr.get("/sign-in", status_code=status.HTTP_200_OK)
async def get_sign_in(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "sign-in.html")


@ssr.get("/sign-out", status_code=status.HTTP_200_OK)
async def get_sign_out(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "sign-out.html")


@ssr.get("/sign-up", status_code=status.HTTP_200_OK)
async def get_sign_up(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "sign-up.html")


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
