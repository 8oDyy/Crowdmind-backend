from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


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


ERROR_STATUS_MAP: dict[type[AppError], int] = {
    NotFoundError: 404,
    ValidationError: 422,
    StorageError: 502,
    RepoError: 500,
    ConflictError: 409,
}


def create_error_response(status_code: int, message: str, details: Any = None) -> dict:
    response = {"error": {"message": message, "status_code": status_code}}
    if details is not None:
        response["error"]["details"] = details
    return response


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    status_code = ERROR_STATUS_MAP.get(type(exc), 500)
    return JSONResponse(
        status_code=status_code,
        content=create_error_response(status_code, exc.message, exc.details),
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(exc.status_code, exc.detail),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=create_error_response(500, "Internal server error"),
    )
