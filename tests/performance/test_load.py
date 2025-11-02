import asyncio
import time
from statistics import mean, median
from typing import List

import aiohttp
import pytest


class LoadTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[float] = []

    async def single_request(self, session: aiohttp.ClientSession, endpoint: str) -> float:
        start = time.time()
        try:
            async with session.get(f"{self.base_url}{endpoint}") as response:
                await response.json()
                return time.time() - start
        except Exception:
            return -1  # Error marker

    async def load_test(self, endpoint: str, concurrent_users: int, requests_per_user: int):
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=50)
        timeout = aiohttp.ClientTimeout(total=30)

        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = []
            for _ in range(concurrent_users):
                for _ in range(requests_per_user):
                    tasks.append(self.single_request(session, endpoint))

            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time

            # Filter successful requests
            successful = [r for r in results if isinstance(r, float) and r > 0]
            failed = len(results) - len(successful)

            return {
                "total_requests": len(results),
                "successful_requests": len(successful),
                "failed_requests": failed,
                "total_time": total_time,
                "requests_per_second": len(successful) / total_time if total_time > 0 else 0,
                "avg_response_time": mean(successful) if successful else 0,
                "median_response_time": median(successful) if successful else 0,
                "min_response_time": min(successful) if successful else 0,
                "max_response_time": max(successful) if successful else 0
            }


@pytest.mark.asyncio
async def test_health_endpoint_load():
    """Load test health endpoint with 10 concurrent users, 5 requests each."""
    tester = LoadTester()
    results = await tester.load_test("/health", concurrent_users=10, requests_per_user=5)

    assert results["failed_requests"] == 0
    assert results["requests_per_second"] > 50
    assert results["avg_response_time"] < 0.1


@pytest.mark.asyncio
async def test_puzzle_solve_load():
    """Load test puzzle solve endpoint with authentication."""
    # First get auth token
    async with aiohttp.ClientSession() as session:
        auth = aiohttp.BasicAuth("admin", "secret123")
        async with session.post("http://localhost:8000/auth/token", auth=auth) as response:
            token_data = await response.json()
            token = token_data["access_token"]

    # Load test with token
    class AuthLoadTester(LoadTester):
        async def single_request(self, session: aiohttp.ClientSession, endpoint: str) -> float:
            headers = {"Authorization": f"Bearer {token}"}
            start = time.time()
            try:
                async with session.get(f"{self.base_url}{endpoint}", headers=headers) as response:
                    await response.json()
                    return time.time() - start
            except Exception:
                return -1

    tester = AuthLoadTester()
    results = await tester.load_test("/v1/puzzle/solve", concurrent_users=5, requests_per_user=2)

    assert results["failed_requests"] == 0
    assert results["avg_response_time"] < 2.0


@pytest.mark.asyncio
async def test_stress_test():
    """Stress test with high concurrency."""
    tester = LoadTester()
    results = await tester.load_test("/health", concurrent_users=50, requests_per_user=10)

    # Allow some failures under stress
    success_rate = results["successful_requests"] / results["total_requests"]
    assert success_rate > 0.95  # 95% success rate
    assert results["requests_per_second"] > 100
