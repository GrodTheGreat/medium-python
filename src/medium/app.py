import pathlib
import time
from typing import Annotated, Callable
from uuid import uuid4

from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.templating import Jinja2Templates

from medium.auth.dependencies import get_current_user
from medium.auth.exceptions import (
    InvalidCredentialsException,
    PasswordMismatchException,
)
from medium.auth.router import api_router, auth_router
from medium.exceptions import MediumException, ValidationException
from medium.users.entity import User
from medium.users.exceptions import EmailConflictException, UsernameConflictException

BASE_DIR = pathlib.Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"

app = FastAPI()
templates = Jinja2Templates(TEMPLATES_DIR)


@app.exception_handler(EmailConflictException)
async def email_conflict_exception_handler(
    _: Request,
    exc: EmailConflictException,
) -> JSONResponse:
    return JSONResponse(
        content={"message": exc.message},
        status_code=status.HTTP_409_CONFLICT,
    )


@app.exception_handler(InvalidCredentialsException)
async def invalid_credentials_exception_handler(
    _: Request,
    exc: InvalidCredentialsException,
) -> JSONResponse:
    return JSONResponse(
        content={"message": exc.message},
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


@app.exception_handler(PasswordMismatchException)
async def password_mismatch_exception_handler(
    _: Request, exc: PasswordMismatchException
) -> JSONResponse:
    return JSONResponse(
        content={"message": exc.message},
        status_code=status.HTTP_400_BAD_REQUEST,
    )


@app.exception_handler(UsernameConflictException)
async def username_conflict_exception_handler(
    _: Request,
    exc: UsernameConflictException,
) -> JSONResponse:
    return JSONResponse(
        content={"message": exc.message},
        status_code=status.HTTP_409_CONFLICT,
    )


@app.exception_handler(ValidationException)
async def validation_exception_handler(
    _: Request, exc: ValidationException
) -> JSONResponse:
    return JSONResponse(
        content={"message": exc.message},
        status_code=status.HTTP_400_BAD_REQUEST,
    )


@app.exception_handler(MediumException)
async def internal_server_exception_handler(
    _: Request, exc: MediumException
) -> JSONResponse:
    return JSONResponse(
        content={"message": exc.message},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


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
