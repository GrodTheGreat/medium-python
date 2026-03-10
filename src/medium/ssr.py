import json
import pathlib
from typing import Annotated

from fastapi import APIRouter, Path, Request, status
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from medium.database import Article, engine
from medium.exceptions import NotFoundException

BASE_DIR = pathlib.Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"

templates = Jinja2Templates(TEMPLATES_DIR)

ArticleIdRouteParam = Annotated[int, Path(alias="articleId", ge=1)]

ssr = APIRouter()


@ssr.get("/", status_code=status.HTTP_200_OK)
async def get_index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@ssr.get("/new-story", status_code=status.HTTP_200_OK)
async def get_new_story(request: Request):
    return templates.TemplateResponse(request, "editor.html", {"article_content": None})


@ssr.get("/{articleId:int}", status_code=status.HTTP_200_OK)
async def get_article(request: Request, article_id: ArticleIdRouteParam):
    with Session(engine) as db:
        statement = select(Article).where(Article.id == article_id).limit(1)
        article = db.exec(statement).first()
        if article is None:
            raise NotFoundException()
        if article.id is None:
            raise Exception()

    return templates.TemplateResponse(
        request,
        "article.html",
        {"article_html": article.html_content},
    )


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
    namespace: str,
    slug: str,
    article_id: ArticleIdRouteParam,
):
    raise NotImplementedError()
