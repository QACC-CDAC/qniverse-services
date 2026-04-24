"""Custom exceptions for the application"""

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi.errors import RateLimitExceeded
from datetime import datetime
from typing import Dict, Any

from src.models import ErrorResponse
from src.utils.logger import logger


class TranspilerError(Exception):
    """Base exception for transpiler-related errors"""

    pass


class ValidationError(Exception):
    """Exception for validation errors"""

    pass


class LanguageNotSupportedError(TranspilerError):
    """Exception for unsupported language pairs"""

    pass


class TranspilationTimeoutError(TranspilerError):
    """Exception for transpilation timeout"""

    pass

class PackageInstallationError(Exception):
    """Exception for package installation errors"""

    pass

def setup_exception_handlers(app: FastAPI):
    """Register custom exception handlers"""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        request_id = getattr(request.state, "request_id", None)

        logger.warning(
            f"HTTP exception: {exc.status_code} - {exc.detail}",
            extra={"request_id": request_id, "path": request.url.path},
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=jsonable_encoder(
                ErrorResponse(
                    request_id=request_id,
                    error_code=f"HTTP_{exc.status_code}",
                    error_message=str(exc.detail),
                    timestamp=datetime.utcnow().isoformat(),
                    path=request.url.path,
                ).model_dump()
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        request_id = getattr(request.state, "request_id", None)

        logger.warning(
            "Validation error: {}",
            str(exc.errors()),
            extra={"request_id": request_id, "path": request.url.path},
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder(
                ErrorResponse(
                    request_id=request_id,
                    error_code="VALIDATION_ERROR",
                    error_message="Request validation failed",
                    details={"errors": exc.errors()},
                    timestamp=datetime.utcnow().isoformat(),
                    path=request.url.path,
                ).model_dump()
            ),
        )

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
        request_id = getattr(request.state, "request_id", None)

        logger.warning(
            f"Rate limit exceeded for {request.client.host}",
            extra={"request_id": request_id, "path": request.url.path},
        )

        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=jsonable_encoder(
                ErrorResponse(
                    request_id=request_id,
                    error_code="RATE_LIMIT_EXCEEDED",
                    error_message="Too many requests. Please try again later.",
                    timestamp=datetime.utcnow().isoformat(),
                    path=request.url.path,
                ).model_dump()
            ),
            headers={"Retry-After": "60"},
        )

    @app.exception_handler(TranspilerError)
    async def transpiler_exception_handler(request: Request, exc: TranspilerError):
        request_id = getattr(request.state, "request_id", None)

        logger.error(
            f"Transpiler error: {str(exc)}",
            extra={"request_id": request_id, "path": request.url.path},
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder(
                ErrorResponse(
                    request_id=request_id,
                    error_code="TRANSPILER_ERROR",
                    error_message=str(exc),
                    timestamp=datetime.utcnow().isoformat(),
                    path=request.url.path,
                ).model_dump()
            ),
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        request_id = getattr(request.state, "request_id", None)

        logger.warning(
            f"Validation error: {str(exc)}",
            extra={"request_id": request_id, "path": request.url.path},
        )

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=jsonable_encoder(
                ErrorResponse(
                    request_id=request_id,
                    error_code="VALIDATION_ERROR",
                    error_message=str(exc),
                    timestamp=datetime.utcnow().isoformat(),
                    path=request.url.path,
                ).model_dump()
            ),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", None)

        logger.exception(
            f"Unhandled exception: {str(exc)}",
            extra={"request_id": request_id, "path": request.url.path},
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder(
                ErrorResponse(
                    request_id=request_id,
                    error_code="INTERNAL_SERVER_ERROR",
                    error_message="An unexpected error occurred. Please try again later.",
                    timestamp=datetime.utcnow().isoformat(),
                    path=request.url.path,
                ).model_dump()
            ),
        )
