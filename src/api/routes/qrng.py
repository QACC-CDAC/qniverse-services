"""Transpilation endpoint routes"""

from fastapi import APIRouter, Depends, Request, HTTPException, status, BackgroundTasks
from typing import Optional
import asyncio

from src.models import QRNGRequest, QRNGResponse, CloudQRNGRequest, CloudQRNGResponse
from src.services.qrng_service import qrng_service

from src.api.dependencies.auth import verify_api_key
from src.middleware.rate_limit import limiter
from src.utils.logger import logger
from src.core.exceptions import QRNGError, ValidationError
from src.config import get_settings


router = APIRouter()
settings = get_settings()


@router.post(
    "/",
    response_model=QRNGResponse,
    dependencies=[Depends(verify_api_key)],
    summary="Generate Quantum Random Numbers",
    description="Generate a list of quantum random numbers with optional post-processing"
)
@limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/{settings.RATE_LIMIT_PERIOD}second")
async def generate_qrng(request:Request,qrng_request: QRNGRequest)-> QRNGResponse:
    try:
        result =  qrng_service.generate_random_numbers(count=qrng_request.count, post_processing=qrng_request.post_processing)
        return QRNGResponse(**result)
    except QRNGError as e:
        logger.error(f"QRNG generation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except ValidationError as e:
        logger.error(f"QRNG validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    

@router.post(
    "/bits",
    response_model=CloudQRNGResponse,
    dependencies=[Depends(verify_api_key)],
    summary="Generate Quantum Random Numbers",
    description="Generate a list of quantum random numbers with optional post-processing"
)
@limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/{settings.RATE_LIMIT_PERIOD}second")
async def generate_qrng(request:Request,cloud_qrng_request: CloudQRNGRequest)-> CloudQRNGResponse:
    try:
        result =  qrng_service.get_bits(count=cloud_qrng_request.count)
        response = CloudQRNGResponse(**result)
        logger.error(f"here is the response: {response}")
        return response
    except QRNGError as e:
        logger.error(f"QRNG generation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except ValidationError as e:
        logger.error(f"QRNG validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))