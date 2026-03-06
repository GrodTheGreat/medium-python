from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from medium.api import api
from medium.exceptions import NotFoundException
from medium.ssr import ssr

app = FastAPI()


@app.exception_handler(NotFoundException)
async def handle_not_found_exception(
    _: Request, exec: NotFoundException
) -> JSONResponse:
    return JSONResponse(
        content={"error": exec.message},
        status_code=status.HTTP_404_NOT_FOUND,
    )


@app.exception_handler(Exception)
async def handle_exception(_: Request, exec: Exception) -> JSONResponse:
    return JSONResponse(
        content={"error": "internal server error"},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


app.include_router(ssr)
app.include_router(api, prefix="/api")
