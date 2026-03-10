from typing import Annotated

from fastapi import APIRouter, Path, status
from sqlmodel import Session, select

from medium.database import Article, engine
from medium.exceptions import NotFoundException
from medium.schemas import BaseSchema


class ArticleContentResponse(BaseSchema):
    id: int
    content: str


class ArticleInfoResponse(BaseSchema):
    id: int
    title: str


class ArticleMarkdownResponse(BaseSchema):
    id: int
    markdown: str


class ArticleHTMLResponse(BaseSchema):
    id: int
    html: str


api = APIRouter()

ArticleIdRouteParam = Annotated[int, Path(alias="articleId", ge=1)]


@api.get("/articles/{articleId:int}", status_code=status.HTTP_200_OK)
async def get_article_info_api(article_id: ArticleIdRouteParam):
    with Session(engine) as db:
        statement = select(Article).where(Article.id == article_id).limit(1)
        article = db.exec(statement).first()
        if article is None:
            raise NotFoundException()
        if article.id is None:
            raise Exception()

    return ArticleInfoResponse(id=article.id, title=article.title)


@api.get("/articles/{articleId:int}/assets", status_code=status.HTTP_200_OK)
async def get_article_assets_api(article_id: ArticleIdRouteParam):
    raise NotImplementedError()


@api.get("/articles/{articleId:int}/comments", status_code=status.HTTP_200_OK)
async def get_article_comments_api(article_id: ArticleIdRouteParam):
    raise NotImplementedError()


@api.get("/articles/{articleId:int}/content", status_code=status.HTTP_200_OK)
async def get_article_content_api(
    article_id: ArticleIdRouteParam,
) -> ArticleContentResponse:
    with Session(engine) as db:
        statement = select(Article).where(Article.id == article_id).limit(1)
        article = db.exec(statement).first()
        if article is None:
            raise NotFoundException()
        if article.id is None:
            raise Exception()

    return ArticleContentResponse(id=article.id, content=article.text_content)


@api.get("/articles/{articleId:int}/fans", status_code=status.HTTP_200_OK)
async def get_article_fans_api(article_id: ArticleIdRouteParam):
    raise NotImplementedError()


@api.get("/articles/{articleId:int}/html", status_code=status.HTTP_200_OK)
async def get_article_html_api(article_id: ArticleIdRouteParam) -> ArticleHTMLResponse:
    with Session(engine) as db:
        statement = select(Article).where(Article.id == article_id).limit(1)
        article = db.exec(statement).first()
        if article is None:
            raise NotFoundException()
        if article.id is None:
            raise Exception()

    return ArticleHTMLResponse(id=article.id, html=article.html_content)


@api.get("/articles/{articleId:int}/markdown", status_code=status.HTTP_200_OK)
async def get_article_markdown_api(
    article_id: ArticleIdRouteParam,
) -> ArticleMarkdownResponse:
    with Session(engine) as db:
        statement = select(Article).where(Article.id == article_id).limit(1)
        article = db.exec(statement).first()
        if article is None:
            raise NotFoundException()
        if article.id is None:
            raise Exception()

    return ArticleMarkdownResponse(id=article.id, markdown=article.markdown_content)


@api.get("/articles/{articleId:int}/recommended", status_code=status.HTTP_200_OK)
async def get_article_recommended_api(article_id: ArticleIdRouteParam):
    raise NotImplementedError()


@api.get("/articles/{articleId:int}/related", status_code=status.HTTP_200_OK)
async def get_article_related_api(article_id: ArticleIdRouteParam):
    raise NotImplementedError()
