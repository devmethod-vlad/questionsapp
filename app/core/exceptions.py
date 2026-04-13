"""Global exception and validation handlers.

For API compatibility we avoid FastAPI default 422 schema and map
validation issues into legacy error envelope.
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError

from app.responses.builders import error


class LegacyHTTPException(Exception):
    """Custom exception that carries legacy error message + status code."""

    def __init__(self, message: str, status_code: int = 200):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(LegacyHTTPException)
    async def handle_legacy_exception(_: Request, exc: LegacyHTTPException):
        return error(exc.message, status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(_: Request, __: RequestValidationError):
        return error("WARN: Invalid request payload", status_code=400)

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(_: Request, __: Exception):
        return error("Internal server error while processing request.", status_code=500)
