from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

logger = get_logger(__name__)


class AppError(Exception):
    def __init__(self, message: str, details: Any = None):
        self.message = message
        self.details = details
        super().__init__(message)


class NotFoundError(AppError):
    pass


class ValidationError(AppError):
    pass


class StorageError(AppError):
    pass


class RepoError(AppError):
    pass


class ConflictError(AppError):
    pass


class PiError(AppError):
    pass


ERROR_STATUS_MAP: dict[type[AppError], int] = {
    NotFoundError: 404,
    ValidationError: 422,
    StorageError: 502,
    RepoError: 500,
    ConflictError: 409,
    PiError: 502,
}


def create_error_response(status_code: int, message: str, details: Any = None) -> dict:
    response = {"error": {"message": message, "status_code": status_code}}
    if details is not None:
        response["error"]["details"] = details
    return response


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    status_code = ERROR_STATUS_MAP.get(type(exc), 500)
    log = logger.exception if status_code >= 500 else logger.warning
    log(
        "%s on %s %s: %s",
        type(exc).__name__,
        request.method,
        request.url.path,
        exc.message,
    )
    return JSONResponse(
        status_code=status_code,
        content=create_error_response(status_code, exc.message, exc.details),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if exc.status_code >= 500:
        logger.error(
            "HTTPException %s on %s %s: %s",
            exc.status_code,
            request.method,
            request.url.path,
            exc.detail,
        )
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(exc.status_code, exc.detail),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "Unhandled %s on %s %s",
        type(exc).__name__,
        request.method,
        request.url.path,
    )
    return JSONResponse(
        status_code=500,
        content=create_error_response(500, "Internal server error"),
    )
