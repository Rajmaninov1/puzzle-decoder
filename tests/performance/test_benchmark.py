import asyncio
import time

import pytest

from puzzle_solver.domain.services.fragment import FragmentService
from puzzle_solver.domain.services.puzzle import PuzzleService


class BenchmarkTester:
    def __init__(self):
        self.results = {}

    def time_function(self, func_name: str):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                start = time.perf_counter()
                result = await func(*args, **kwargs)
                elapsed = time.perf_counter() - start
                self.results[func_name] = elapsed
                return result

            return wrapper

        return decorator


@pytest.mark.asyncio
async def test_fragment_service_benchmark():
    """Benchmark fragment service operations."""
    benchmark = BenchmarkTester()
    service = FragmentService()

    @benchmark.time_function("single_fragment")
    async def test_single():
        return await service.get_fragment(1)

    @benchmark.time_function("fragment_batch")
    async def test_batch():
        return await service.get_fragments_batch([1, 2, 3, 4, 5])

    @benchmark.time_function("fragment_discovery")
    async def test_discovery():
        return await service.discover_fragments(initial_batch_size=5)

    # Run benchmarks
    await test_single()
    await test_batch()
    await test_discovery()

    # Assertions
    assert benchmark.results["single_fragment"] < 1.0
    assert benchmark.results["fragment_batch"] < 2.0
    assert benchmark.results["fragment_discovery"] < 3.0

    print(f"Benchmark Results:")
    for test, time_taken in benchmark.results.items():
        print(f"  {test}: {time_taken:.3f}s")


@pytest.mark.asyncio
async def test_puzzle_service_benchmark():
    """Benchmark complete puzzle solving."""
    benchmark = BenchmarkTester()
    service = PuzzleService()

    @benchmark.time_function("complete_puzzle_solve")
    async def test_solve():
        text, elapsed, stats = await service.solve_puzzle()
        return text, elapsed, stats

    # Run multiple times for average
    times = []
    for _ in range(3):
        result = await test_solve()
        times.append(benchmark.results["complete_puzzle_solve"])

    avg_time = sum(times) / len(times)
    assert avg_time < 2.0  # Should solve in under 2 seconds

    print(f"Puzzle solve average time: {avg_time:.3f}s")
    print(f"Individual runs: {[f'{t:.3f}s' for t in times]}")


@pytest.mark.asyncio
async def test_concurrent_puzzle_solving():
    """Test multiple concurrent puzzle solves."""
    service = PuzzleService()

    async def solve_puzzle():
        start = time.perf_counter()
        await service.solve_puzzle()
        return time.perf_counter() - start

    # Run 5 concurrent puzzle solves
    start_time = time.perf_counter()
    tasks = [solve_puzzle() for _ in range(5)]
    results = await asyncio.gather(*tasks)
    total_time = time.perf_counter() - start_time

    # All should complete
    assert len(results) == 5
    assert all(r > 0 for r in results)

    # Concurrent execution should be faster than sequential
    sequential_time = sum(results)
    efficiency = sequential_time / total_time

    print(f"Concurrent efficiency: {efficiency:.2f}x")
    print(f"Total time: {total_time:.3f}s")
    print(f"Sequential would take: {sequential_time:.3f}s")

    assert efficiency > 2.0  # Should be at least 2x faster
