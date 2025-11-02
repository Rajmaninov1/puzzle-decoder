import time
import uuid

from fastapi import Request

from puzzle_solver.api.versioning import get_api_version, validate_version
from puzzle_solver.core.observability import correlation_id, request_counter, request_duration


async def observability_middleware(request: Request, call_next):
    """Add observability and versioning to all requests."""
    from opentelemetry import trace

    # Set correlation ID
    cid = request.headers.get('x-correlation-id') or str(uuid.uuid4())
    correlation_id.set(cid)

    # Add correlation ID to current span
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.set_attribute("correlation_id", cid)
        current_span.set_attribute("http.correlation_id", cid)

    # API versioning
    try:
        api_version = get_api_version(request)
        validate_version(api_version)
    except Exception:  # noqa
        api_version = "v1"  # Fallback to v1

    # Metrics
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    request_counter.labels(method=request.method, endpoint=request.url.path).inc()
    request_duration.observe(duration)

    response.headers['x-correlation-id'] = cid
    response.headers['api-version'] = api_version
    response.headers['x-request-start-time'] = str(start_time)
    response.headers['x-request-duration'] = f"{duration:.6f}"
    return response
