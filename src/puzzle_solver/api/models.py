from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class ReadyResponse(BaseModel):
    status: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class PuzzleStats(BaseModel):
    total_found: int
    completion_percentage: float
    total_requests: int
    missing_count: int


class PuzzleSolveResponse(BaseModel):
    puzzle_text: str
    elapsed_seconds: float
    stats: PuzzleStats
    api_version: str
    user: str
