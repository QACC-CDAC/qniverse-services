"""Transpilation endpoint routes"""

from fastapi import APIRouter, Depends, Request, HTTPException, status, BackgroundTasks
from typing import Optional
import asyncio

from src.models import TranspileRequest, TranspileResponse
from src.services.transpilation_service import TranspilationService
from src.services.cache_service import cache_service
from src.api.dependencies.auth import verify_api_key
from src.middleware.rate_limit import limiter
from src.utils.logger import logger
from src.core.exceptions import TranspilerError, ValidationError
from src.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post(
    "/",
    response_model=TranspileResponse,
    status_code=status.HTTP_200_OK,
    summary="Transpile code",
    description="""
    Transpile source code from one programming language to another.
    
    ## Supported language pairs:
    - Python → JavaScript, TypeScript, Go, Java, Rust, C#
    - JavaScript → Python, TypeScript, Java, Go
    - TypeScript → Python, JavaScript, Go
    - Java → Python, JavaScript, Go, C#
    - Go → Python, JavaScript, TypeScript
    - Rust → Python, JavaScript, C#
    - C# → Python, JavaScript, Java, Go
    
    ## Example request:
    ```json
    {
        "source_code": "def greet(name):\\n    return f'Hello {name}'",
        "source_lang": "python",
        "target_lang": "javascript",
        "options": {
            "format_code": true,
            "optimization_level": 1
        }
    }
    ```
    """
)
@limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/{settings.RATE_LIMIT_PERIOD}second")
async def transpile_code(
    request: Request,
    transpile_request: TranspileRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key),
    service: TranspilationService = Depends()
) -> TranspileResponse:
    """
    Transpile source code from source language to target language
    """
    request_id = getattr(request.state, "request_id", None)

    # Generate cache key
    cache_key = cache_service.generate_key(
        transpile_request.source_code,
        transpile_request.source_lang,
        transpile_request.target_lang,
        transpile_request.options.model_dump()
    )

    # Check cache
    if settings.ENABLE_CACHE:
        cached_response = await cache_service.get(cache_key)
        if cached_response:
            logger.info(f"Cache hit for request {request_id}")
            cached_response["cached"] = True
            return TranspileResponse(**cached_response)

    try:
        # Validate input size
        if len(transpile_request.source_code) > settings.MAX_CODE_LENGTH:
            raise ValidationError(
                f"Source code exceeds maximum length of {settings.MAX_CODE_LENGTH} characters"
            )

        # Perform transpilation with timeout
        try:
            transpiled_code, warnings, errors, execution_time = await asyncio.wait_for(
                service.transpile(
                    source_code=transpile_request.source_code,
                    source_lang=transpile_request.source_lang,
                    target_lang=transpile_request.target_lang,
                    options=transpile_request.options.model_dump()
                ),
                timeout=settings.MAX_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError:
            raise TranspilerError(
                f"Transpilation timeout after {settings.MAX_TIMEOUT_SECONDS} seconds"
            )

        # Prepare response
        success = len(errors) == 0 and bool(transpiled_code)

        response = TranspileResponse(
            request_id=request_id,
            source_lang=transpile_request.source_lang,
            target_lang=transpile_request.target_lang,
            transpiled_code=transpiled_code if success else "",
            warnings=warnings,
            errors=errors,
            execution_time_ms=execution_time,
            success=success,
            metadata={
                "source_length": len(transpile_request.source_code),
                "target_length": len(transpiled_code) if transpiled_code else 0,
                "compression_ratio": (
                    len(transpiled_code) / len(transpile_request.source_code)
                    if transpiled_code and transpile_request.source_code else 0
                ),
                "options_used": transpile_request.options.model_dump()
            },
            cached=False
        )

        # Cache successful response
        if settings.ENABLE_CACHE and success:
            background_tasks.add_task(
                cache_service.set,
                cache_key,
                response.model_dump(),
                ttl=settings.CACHE_TTL_SECONDS
            )

        # Log metrics
        if settings.ENABLE_PERFORMANCE_METRICS:
            logger.info(
                "Transpilation completed",
                extra={
                    "request_id": request_id,
                    "execution_time_ms": execution_time,
                    "source_lang": transpile_request.source_lang,
                    "target_lang": transpile_request.target_lang,
                    "success": success,
                    "source_size": len(transpile_request.source_code),
                    "target_size": len(transpiled_code) if transpiled_code else 0
                }
            )

        return response

    except ValidationError as e:
        logger.warning(
            f"Validation error: {str(e)}",
            extra={"request_id": request_id}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except TranspilerError as e:
        logger.error(
            f"Transpilation error: {str(e)}",
            extra={"request_id": request_id}
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )

    except Exception as e:
        logger.exception(
            f"Unexpected error: {str(e)}",
            extra={"request_id": request_id}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during transpilation"
        )