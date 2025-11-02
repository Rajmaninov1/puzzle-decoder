from datetime import timedelta

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from puzzle_solver.api.auth import create_access_token
from puzzle_solver.api.models import TokenResponse
from puzzle_solver.config.settings import settings

router = APIRouter(prefix="/auth", tags=["authentication"])
basic_auth = HTTPBasic()

# Simple user store (use a database in production)
USERS = {
    "admin": "secret123"
}


@router.post("/token", response_model=TokenResponse)
async def login(credentials: HTTPBasicCredentials = Depends(basic_auth)):
    """Get JWT token with basic auth."""
    username = credentials.username
    if username not in USERS or credentials.password != USERS[username]:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token_expires = timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    return TokenResponse(access_token=access_token, token_type="bearer")
