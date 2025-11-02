from fastapi import APIRouter, Response

from puzzle_solver.core.observability import get_metrics, CONTENT_TYPE_LATEST

router = APIRouter(tags=["observability"])


@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=get_metrics(), media_type=CONTENT_TYPE_LATEST)
