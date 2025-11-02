#!/usr/bin/env python3
"""
Benchmark script for puzzle solver performance.
Usage: python scripts/benchmark.py
"""
import asyncio
import time
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from puzzle_solver.domain.services.puzzle import PuzzleService
from puzzle_solver.domain.services.fragment import FragmentService

class Benchmark:
    def __init__(self):
        self.results = {}
    
    async def time_async_function(self, name: str, func, *args, **kwargs):
        """Time an async function and store result."""
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        self.results[name] = elapsed
        return result
    
    def print_results(self):
        """Print benchmark results."""
        print("\n" + "="*50)
        print("BENCHMARK RESULTS")
        print("="*50)
        for name, elapsed in self.results.items():
            print(f"{name:<30} {elapsed:.3f}s")
        print("="*50)

async def run_fragment_benchmarks():
    """Run fragment service benchmarks."""
    print("Running Fragment Service Benchmarks...")
    benchmark = Benchmark()
    service = FragmentService()
    
    # Single fragment fetch
    await benchmark.time_async_function(
        "Single Fragment", 
        service.get_fragment, 1
    )
    
    # Batch fragment fetch
    await benchmark.time_async_function(
        "Fragment Batch (5)", 
        service.get_fragments_batch, [1, 2, 3, 4, 5]
    )
    
    # Fragment range
    await benchmark.time_async_function(
        "Fragment Range (1-10)", 
        service.get_fragment_range, 1, 10
    )
    
    # Full discovery
    await benchmark.time_async_function(
        "Fragment Discovery", 
        service.discover_fragments, 10
    )
    
    benchmark.print_results()
    return benchmark.results

async def run_puzzle_benchmarks():
    """Run puzzle service benchmarks."""
    print("\nRunning Puzzle Service Benchmarks...")
    benchmark = Benchmark()
    service = PuzzleService()
    
    # Single puzzle solve
    text, elapsed, stats = await benchmark.time_async_function(
        "Complete Puzzle Solve", 
        service.solve_puzzle
    )
    
    print(f"\nPuzzle Stats:")
    print(f"  Fragments found: {stats.get('total_found', 'N/A')}")
    print(f"  Success rate: {stats.get('completion_percentage', 'N/A')}%")
    print(f"  Requests made: {stats.get('total_requests', 'N/A')}")
    
    benchmark.print_results()
    return benchmark.results

async def run_concurrency_test():
    """Test concurrent puzzle solving."""
    print("\nRunning Concurrency Test...")
    service = PuzzleService()
    
    async def solve_single():
        start = time.perf_counter()
        await service.solve_puzzle()
        return time.perf_counter() - start
    
    # Sequential execution
    print("  Sequential execution (3 solves)...")
    sequential_start = time.perf_counter()
    sequential_times = []
    for i in range(3):
        elapsed = await solve_single()
        sequential_times.append(elapsed)
        print(f"    Solve {i+1}: {elapsed:.3f}s")
    sequential_total = time.perf_counter() - sequential_start
    
    # Concurrent execution
    print("  Concurrent execution (3 solves)...")
    concurrent_start = time.perf_counter()
    tasks = [solve_single() for _ in range(3)]
    concurrent_times = await asyncio.gather(*tasks)
    concurrent_total = time.perf_counter() - concurrent_start
    
    print(f"\nConcurrency Results:")
    print(f"  Sequential total: {sequential_total:.3f}s")
    print(f"  Concurrent total: {concurrent_total:.3f}s")
    print(f"  Speedup: {sequential_total/concurrent_total:.2f}x")
    print(f"  Efficiency: {(sequential_total/concurrent_total)/3*100:.1f}%")

async def main():
    """Run all benchmarks."""
    print("Puzzle Solver Performance Benchmark")
    print("=" * 50)
    
    try:
        # Fragment service benchmarks
        fragment_results = await run_fragment_benchmarks()
        
        # Puzzle service benchmarks  
        puzzle_results = await run_puzzle_benchmarks()
        
        # Concurrency test
        await run_concurrency_test()
        
        # Summary
        print("\n" + "="*50)
        print("PERFORMANCE SUMMARY")
        print("="*50)
        
        if fragment_results.get("Fragment Discovery", 0) < 1.0:
            print("✓ Fragment discovery under 1s")
        else:
            print("⚠ Fragment discovery over 1s")
            
        if puzzle_results.get("Complete Puzzle Solve", 0) < 2.0:
            print("✓ Puzzle solve under 2s")
        else:
            print("⚠ Puzzle solve over 2s")
            
        print("="*50)
        
    except Exception as e:
        print(f"Benchmark failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())