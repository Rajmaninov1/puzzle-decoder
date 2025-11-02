from pydantic import BaseModel
from typing import List

class PuzzleStats(BaseModel):
    total_found: int
    missing_count: int
    completion_rate: float
    time_elapsed: float
    fragments_per_second: float
    missing_indices: List[int]
    is_complete: bool
    completion_percentage: float
    total_requests: int

class PuzzleResult(BaseModel):
    puzzle_text: str
    elapsed_seconds: float
    stats: PuzzleStats