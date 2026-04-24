"""Logging middleware for request/response logging"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from src.utils.logger import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all incoming requests and outgoing responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        request_id = getattr(request.state, "request_id", None)
        
        # Log request
        await self._log_request(request, request_id)
        
        try:
            response = await call_next(request)
            
            # Log response
            process_time = (time.time() - start_time) * 1000
            await self._log_response(response, process_time, request_id)
            
            # Add process time header
            response.headers["X-Process-Time-MS"] = str(int(process_time))
            
            return response
            
        except Exception:
            raise
    
    async def _log_request(self, request: Request, request_id: str):
        """Log request details"""
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        logger.bind(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=client_ip,
            user_agent=user_agent,
            query_params=str(request.query_params),
        ).info(f"Request: {request.method} {request.url.path}")
    
    async def _log_response(self, response: Response, process_time: float, request_id: str):
        """Log response details"""
        logger.bind(
            request_id=request_id,
            status_code=response.status_code,
            duration_ms=round(process_time, 2),
        ).info(f"Response: {response.status_code} - {process_time:.2f}ms")