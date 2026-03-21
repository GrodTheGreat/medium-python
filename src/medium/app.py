import pathlib
import time
from typing import Annotated, Callable
from uuid import uuid4

from fastapi import Depends, FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from medium.auth.dependencies import get_current_user
from medium.auth.router import api_router, auth_router
from medium.users.entity import User

BASE_DIR = pathlib.Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"

app = FastAPI()
templates = Jinja2Templates(TEMPLATES_DIR)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next: Callable) -> Response:
    request_id = uuid4()
    request.state.request_id = request_id
    response: Response = await call_next(request)
    response.headers["Medium-Request-Id"] = str(request.state.request_id)
    return response


@app.middleware("http")
async def request_timing_middleware(request: Request, call_next: Callable) -> Response:
    start = time.perf_counter()
    response: Response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1_000
    response.headers["Response-Time"] = f"{duration_ms:.2f}ms"
    return response


@app.get("/")
async def get_index(
    request: Request, user: Annotated[User | None, Depends(get_current_user)]
) -> HTMLResponse:
    context = {"current_user": user}
    return templates.TemplateResponse(request, "index.html", context)


app.include_router(auth_router)
app.include_router(api_router, prefix="/api")
