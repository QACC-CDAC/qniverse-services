"""Prometheus metrics setup"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
from typing import Dict, Optional
import time

# Define metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
)

TRANSPILATION_COUNT = Counter(
    'transpilation_total',
    'Total transpilations',
    ['source_lang', 'target_lang', 'success']
)

TRANSPILATION_DURATION = Histogram(
    'transpilation_duration_seconds',
    'Transpilation duration in seconds',
    ['source_lang', 'target_lang'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10, 30]
)

ACTIVE_REQUESTS = Gauge(
    'active_requests',
    'Active HTTP requests'
)

CACHE_HITS = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

CACHE_MISSES = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)


def setup_metrics(app):
    """Setup metrics middleware"""
    
    @app.middleware("http")
    async def metrics_middleware(request, call_next):
        ACTIVE_REQUESTS.inc()
        
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        ACTIVE_REQUESTS.dec()
        
        # Record metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        return response
    
    @app.get("/metrics")
    async def get_metrics():
        """Prometheus metrics endpoint"""
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )


def record_transpilation_metrics(
    source_lang: str, 
    target_lang: str, 
    duration: float, 
    success: bool
):
    """Record transpilation metrics"""
    TRANSPILATION_COUNT.labels(
        source_lang=source_lang,
        target_lang=target_lang,
        success=success
    ).inc()
    
    TRANSPILATION_DURATION.labels(
        source_lang=source_lang,
        target_lang=target_lang
    ).observe(duration)


def record_cache_metrics(hit: bool, cache_type: str = "transpilation"):
    """Record cache hit/miss metrics"""
    if hit:
        CACHE_HITS.labels(cache_type=cache_type).inc()
    else:
        CACHE_MISSES.labels(cache_type=cache_type).inc()