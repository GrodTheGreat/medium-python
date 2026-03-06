from typing import Annotated

from fastapi import APIRouter, Path, status
from sqlmodel import Session, select

from medium.database import Post, engine
from medium.exceptions import NotFoundException
from medium.schemas import BaseSchema


class PostContentResponse(BaseSchema):
    id: int
    content: str


class PostInfoResponse(BaseSchema):
    id: int
    title: str


class PostMarkdownResponse(BaseSchema):
    id: int
    markdown: str


class PostHTMLResponse(BaseSchema):
    id: int
    html: str


api = APIRouter()

PostIdRouteParam = Annotated[int, Path(alias="postId", ge=1)]


@api.get("/posts/{postId:int}", status_code=status.HTTP_200_OK)
async def get_post_info_api(post_id: PostIdRouteParam):
    with Session(engine) as db:
        statement = select(Post).where(Post.id == post_id).limit(1)
        post = db.exec(statement).first()
        if post is None:
            raise NotFoundException()
        if post.id is None:
            raise Exception()

    return PostInfoResponse(id=post.id, title=post.title)


@api.get("/posts/{postId:int}/assets", status_code=status.HTTP_200_OK)
async def get_post_assets_api(post_id: PostIdRouteParam):
    raise NotImplementedError()


@api.get("/posts/{postId:int}/comments", status_code=status.HTTP_200_OK)
async def get_post_comments_api(post_id: PostIdRouteParam):
    raise NotImplementedError()


@api.get("/posts/{postId:int}/content", status_code=status.HTTP_200_OK)
async def get_post_content_api(post_id: PostIdRouteParam) -> PostContentResponse:
    with Session(engine) as db:
        statement = select(Post).where(Post.id == post_id).limit(1)
        post = db.exec(statement).first()
        if post is None:
            raise NotFoundException()
        if post.id is None:
            raise Exception()

    return PostContentResponse(id=post.id, content=post.text_content)


@api.get("/posts/{postId:int}/fans", status_code=status.HTTP_200_OK)
async def get_post_fans_api(post_id: PostIdRouteParam):
    raise NotImplementedError()


@api.get("/posts/{postId:int}/html", status_code=status.HTTP_200_OK)
async def get_post_html_api(post_id: PostIdRouteParam) -> PostHTMLResponse:
    with Session(engine) as db:
        statement = select(Post).where(Post.id == post_id).limit(1)
        post = db.exec(statement).first()
        if post is None:
            raise NotFoundException()
        if post.id is None:
            raise Exception()

    return PostHTMLResponse(id=post.id, html=post.html_content)


@api.get("/posts/{postId:int}/markdown", status_code=status.HTTP_200_OK)
async def get_post_markdown_api(post_id: PostIdRouteParam) -> PostMarkdownResponse:
    with Session(engine) as db:
        statement = select(Post).where(Post.id == post_id).limit(1)
        post = db.exec(statement).first()
        if post is None:
            raise NotFoundException()
        if post.id is None:
            raise Exception()

    return PostMarkdownResponse(id=post.id, markdown=post.markdown_content)


@api.get("/posts/{postId:int}/recommended", status_code=status.HTTP_200_OK)
async def get_post_recommended_api(post_id: PostIdRouteParam):
    raise NotImplementedError()


@api.get("/posts/{postId:int}/related", status_code=status.HTTP_200_OK)
async def get_post_related_api(post_id: PostIdRouteParam):
    raise NotImplementedError()
