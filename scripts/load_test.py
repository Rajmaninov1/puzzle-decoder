#!/usr/bin/env python3
"""
Load testing script for puzzle solver API.
Usage: python scripts/load_test.py --users 10 --requests 100 --endpoint /health
"""
import asyncio
import argparse
import time
from typing import Dict, Any
import aiohttp
from statistics import mean, median, stdev

class LoadTestRunner:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
    
    async def make_request(self, session: aiohttp.ClientSession, endpoint: str, headers: Dict = None) -> Dict[str, Any]:
        start = time.perf_counter()
        try:
            async with session.get(f"{self.base_url}{endpoint}", headers=headers) as response:
                status = response.status
                await response.text()  # Consume response
                elapsed = time.perf_counter() - start
                return {"success": True, "status": status, "time": elapsed}
        except Exception as e:
            elapsed = time.perf_counter() - start
            return {"success": False, "error": str(e), "time": elapsed}
    
    async def run_load_test(self, endpoint: str, concurrent_users: int, requests_per_user: int, auth_token: str = None):
        headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else None
        
        connector = aiohttp.TCPConnector(limit=200, limit_per_host=100)
        timeout = aiohttp.ClientTimeout(total=60)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            print(f"Starting load test: {concurrent_users} users, {requests_per_user} requests each")
            print(f"Target: {endpoint}")
            
            tasks = []
            for user in range(concurrent_users):
                for req in range(requests_per_user):
                    tasks.append(self.make_request(session, endpoint, headers))
            
            start_time = time.perf_counter()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.perf_counter() - start_time
            
            return self.analyze_results(results, total_time)
    
    def analyze_results(self, results, total_time: float) -> Dict[str, Any]:
        successful = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed = len(results) - len(successful)
        
        if successful:
            response_times = [r["time"] for r in successful]
            status_codes = {}
            for r in successful:
                status = r.get("status", "unknown")
                status_codes[status] = status_codes.get(status, 0) + 1
        else:
            response_times = []
            status_codes = {}
        
        return {
            "total_requests": len(results),
            "successful_requests": len(successful),
            "failed_requests": failed,
            "success_rate": len(successful) / len(results) * 100,
            "total_time": total_time,
            "requests_per_second": len(successful) / total_time if total_time > 0 else 0,
            "avg_response_time": mean(response_times) if response_times else 0,
            "median_response_time": median(response_times) if response_times else 0,
            "min_response_time": min(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "std_response_time": stdev(response_times) if len(response_times) > 1 else 0,
            "status_codes": status_codes
        }
    
    def print_results(self, results: Dict[str, Any]):
        print("\n" + "="*60)
        print("LOAD TEST RESULTS")
        print("="*60)
        print(f"Total Requests:      {results['total_requests']}")
        print(f"Successful:          {results['successful_requests']}")
        print(f"Failed:              {results['failed_requests']}")
        print(f"Success Rate:        {results['success_rate']:.2f}%")
        print(f"Total Time:          {results['total_time']:.3f}s")
        print(f"Requests/Second:     {results['requests_per_second']:.2f}")
        print("\nResponse Times:")
        print(f"  Average:           {results['avg_response_time']*1000:.2f}ms")
        print(f"  Median:            {results['median_response_time']*1000:.2f}ms")
        print(f"  Min:               {results['min_response_time']*1000:.2f}ms")
        print(f"  Max:               {results['max_response_time']*1000:.2f}ms")
        print(f"  Std Dev:           {results['std_response_time']*1000:.2f}ms")
        
        if results['status_codes']:
            print("\nStatus Codes:")
            for status, count in results['status_codes'].items():
                print(f"  {status}: {count}")

async def get_auth_token(base_url: str) -> str:
    """Get authentication token for protected endpoints."""
    async with aiohttp.ClientSession() as session:
        auth = aiohttp.BasicAuth("admin", "secret123")
        async with session.post(f"{base_url}/auth/token", auth=auth) as response:
            if response.status == 200:
                data = await response.json()
                return data["access_token"]
            else:
                raise Exception(f"Failed to get auth token: {response.status}")

async def main():
    parser = argparse.ArgumentParser(description="Load test puzzle solver API")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL")
    parser.add_argument("--users", type=int, default=10, help="Concurrent users")
    parser.add_argument("--requests", type=int, default=10, help="Requests per user")
    parser.add_argument("--endpoint", default="/health", help="Endpoint to test")
    parser.add_argument("--auth", action="store_true", help="Use authentication")
    
    args = parser.parse_args()
    
    runner = LoadTestRunner(args.url)
    
    auth_token = None
    if args.auth:
        print("Getting authentication token...")
        auth_token = await get_auth_token(args.url)
        print("✓ Authentication token obtained")
    
    results = await runner.run_load_test(
        args.endpoint, 
        args.users, 
        args.requests, 
        auth_token
    )
    
    runner.print_results(results)

if __name__ == "__main__":
    asyncio.run(main())