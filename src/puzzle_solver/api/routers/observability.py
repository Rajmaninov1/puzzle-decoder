from fastapi import APIRouter, Response

from puzzle_solver.core.observability import CONTENT_TYPE_LATEST, get_metrics

router = APIRouter(tags=["observability"])


@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=get_metrics(), media_type=CONTENT_TYPE_LATEST)
