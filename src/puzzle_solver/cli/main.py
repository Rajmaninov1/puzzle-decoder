import asyncio
from typing import Dict, Any

import structlog

from puzzle_solver.clients.http_client import close_http_session
from puzzle_solver.core.logging_config import setup_logging
from puzzle_solver.domain.services.puzzle import PuzzleService


async def main():
    """Main CLI entry point."""
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
        logger.error(f"Failed to solve puzzle: {e}")
    finally:
        await close_http_session()


def _display_results(logger, result) -> None:
    """Display puzzle-solving results."""
    separator = "=" * 60
    
    logger.info(separator)
    logger.info(result.puzzle_text)
    logger.info(separator)
    
    _display_performance_stats(logger, result)
    _display_completion_stats(logger, result)
    
    logger.info(separator)
    logger.info('Less than one second! :D' if result.elapsed_seconds < 1.0 else ':( took more than one second')


def _display_performance_stats(logger, result) -> None:
    """Display performance statistics."""
    logger.info(f"Tiempo: {result.elapsed_seconds:.3f}s | Fragmentos: {result.stats.total_found}")
    logger.info(f"Velocidad: {result.stats.fragments_per_second:.1f} fragments/s")
    logger.info(f"Requests exitosos: {result.stats.total_requests}")


def _display_completion_stats(logger, result) -> None:
    """Display completion statistics."""
    logger.info(f"Completitud: {result.stats.completion_rate:.1%} ({result.stats.completion_percentage:.1f}%)")
    logger.info(f"Fragmentos faltantes: {result.stats.missing_count}")
    logger.info(f"Status: {'Complete' if result.stats.is_complete else 'Incomplete'}")
    
    if result.stats.missing_indices:
        logger.info(f"Missing indices (first 10): {result.stats.missing_indices}")


def cli_main():
    """Synchronous entry point for CLI script."""
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()
