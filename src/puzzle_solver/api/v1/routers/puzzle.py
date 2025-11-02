from fastapi import APIRouter, Depends

from puzzle_solver.api.auth import verify_token
from puzzle_solver.api.models import PuzzleSolveResponse, PuzzleStats
from puzzle_solver.domain.services.puzzle import PuzzleService

router = APIRouter(prefix="/puzzle", tags=["puzzle-v1"])


@router.get("/solve", response_model=PuzzleSolveResponse)
async def solve_puzzle(current_user: str = Depends(verify_token)):
    """Solve the puzzle and return results (v1) - requires JWT token."""
    service = PuzzleService()
    result = await service.solve_puzzle()

    puzzle_stats = PuzzleStats(
        total_found=result.stats.total_found,
        completion_percentage=result.stats.completion_percentage,
        total_requests=result.stats.total_requests,
        missing_count=result.stats.missing_count
    )

    return PuzzleSolveResponse(
        puzzle_text=result.puzzle_text,
        elapsed_seconds=result.elapsed_seconds,
        stats=puzzle_stats,
        api_version="v1",
        user=current_user
    )
