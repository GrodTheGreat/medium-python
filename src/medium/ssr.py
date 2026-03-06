import json
import pathlib
from typing import Annotated

from fastapi import APIRouter, Path, Request, status
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from medium.database import Post, engine
from medium.exceptions import NotFoundException

BASE_DIR = pathlib.Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"

templates = Jinja2Templates(TEMPLATES_DIR)

PostIdRouteParam = Annotated[int, Path(alias="postId", ge=1)]

ssr = APIRouter()


@ssr.get("/", status_code=status.HTTP_200_OK)
async def get_index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@ssr.get("/new-story", status_code=status.HTTP_200_OK)
async def get_new_story(request: Request):
    return templates.TemplateResponse(request, "editor.html", {"post_content": None})


@ssr.get("/{postId:int}", status_code=status.HTTP_200_OK)
async def get_post(request: Request, post_id: PostIdRouteParam):
    with Session(engine) as db:
        statement = select(Post).where(Post.id == post_id).limit(1)
        post = db.exec(statement).first()
        if post is None:
            raise NotFoundException()
        if post.id is None:
            raise Exception()

    return templates.TemplateResponse(
        request,
        "post.html",
        {"post_html": post.html_content},
    )


@ssr.get("/p/{postId:int}/edit", status_code=status.HTTP_200_OK)
async def get_edit_post(request: Request, post_id: PostIdRouteParam):
    with Session(engine) as db:
        statement = select(Post).where(Post.id == post_id).limit(1)
        post = db.exec(statement).first()
        if post is None:
            raise NotFoundException()
        if post.id is None:
            raise Exception()

    return templates.TemplateResponse(
        request,
        "editor.html",
        {"post_content": json.loads(post.json_content) if post.json_content else None},
    )


@ssr.get("/{namespace:str}/{slug:str}-{postId:int}", status_code=status.HTTP_200_OK)
async def get_published_post(namespace: str, slug: str, post_id: PostIdRouteParam):
    raise NotImplementedError()
