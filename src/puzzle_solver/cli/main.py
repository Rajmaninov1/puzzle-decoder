"""
Assumptions:
- Fragment server responds with JSON containing id, index, and text fields
- Fragment indices start from 0 and are consecutive
- Server has random delays between 100-400ms per request
- Total fragments are bounded but unknown count
- Same ID always returns same fragment
- Puzzle completion requires all fragments in sequence
- Maximum concurrency improves performance without overwhelming server
[Lumu Challenge]
"""

import asyncio

import structlog

from puzzle_solver.clients.http_client import close_http_session
from puzzle_solver.core.logging_config import setup_logging
from puzzle_solver.domain.services.puzzle import PuzzleService


async def main():  # Main CLI entry point for puzzle solving execution !!!
    import uuid

    from puzzle_solver.core.observability import correlation_id

    setup_logging()
    # Set correlation ID for CLI operations
    correlation_id.set(str(uuid.uuid4()))

    logger = structlog.get_logger()
    puzzle_service = PuzzleService()

    try:
        result = await puzzle_service.solve_puzzle()
        _display_results(logger, result)
    except Exception as e:
        # guardrail: Handle puzzle solving failures gracefully
        logger.error(f"Failed to solve puzzle: {e}")
    finally:
        await close_http_session()


def _display_results(logger, result) -> None:  # Display comprehensive puzzle solving results and statistics !!!
    separator = "=" * 60

    logger.info(separator)
    logger.info(result.puzzle_text)
    logger.info(separator)

    _display_performance_stats(logger, result)
    _display_completion_stats(logger, result)

    logger.info(separator)
    logger.info("Less than one second! :D" if result.elapsed_seconds < 1.0 else ":( took more than one second")


def _display_performance_stats(logger, result) -> None:  # Display timing and throughput performance metrics !!!
    logger.info(f"Tiempo: {result.elapsed_seconds:.3f}s | Fragmentos: {result.stats.total_found}")
    logger.info(f"Velocidad: {result.stats.fragments_per_second:.1f} fragments/s")
    logger.info(f"Requests exitosos: {result.stats.total_requests}")


def _display_completion_stats(logger, result) -> None:  # Display puzzle completion status and missing fragment info !!!
    logger.info(f"Completitud: {result.stats.completion_rate:.1%} ({result.stats.completion_percentage:.1f}%)")
    logger.info(f"Fragmentos faltantes: {result.stats.missing_count}")
    logger.info(f"Status: {'Complete' if result.stats.is_complete else 'Incomplete'}")

    if result.stats.missing_indices:
        logger.info(f"Missing indices (first 10): {result.stats.missing_indices}")


def cli_main():  # Synchronous entry point wrapper for asyncio execution !!!
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()
