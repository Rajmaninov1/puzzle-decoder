from fastapi import APIRouter, HTTPException

from puzzle_solver.domain.services.fragment import FragmentService
from puzzle_solver.api.models import HealthResponse, ReadyResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health():
    """Liveness probe - basic application health."""
    return HealthResponse(status="ok")


@router.get("/ready", response_model=ReadyResponse)
async def ready():
    """Readiness probe - external service connectivity."""
    try:
        fragment_service = FragmentService()
        await fragment_service.test_connectivity()
        return ReadyResponse(status="ready")
    except Exception:
        raise HTTPException(status_code=503, detail="Service unavailable")
