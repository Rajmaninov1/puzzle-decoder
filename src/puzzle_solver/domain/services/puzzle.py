import time

import structlog

from puzzle_solver.config.settings import PuzzleServiceConfig, settings
from puzzle_solver.core.observability import tracer
from puzzle_solver.domain.models.fragment import FragmentBatch
from puzzle_solver.domain.models.puzzle import PuzzleResult, PuzzleStats
from puzzle_solver.domain.services.fragment import FragmentService


class PuzzleService:
    """Service for solving complete puzzles."""

    def __init__(self, fragment_service: FragmentService | None = None,
                 config: PuzzleServiceConfig | None = None) -> None:  # Initialize puzzle service with fragment service and configuration !!!
        self.config = config or settings.PUZZLE_SERVICE
        self.fragment_service = fragment_service or FragmentService(settings.FRAGMENT_SERVICE)
        self.logger = structlog.get_logger()
        self.logger.info(
            "PuzzleService initialized",
            stream_threshold=self.config.stream_threshold,
            chunk_size=self.config.chunk_size
        )

    async def solve_puzzle(self,
                           stream_threshold: int | None = None) -> PuzzleResult:  # Solve complete puzzle by discovering fragments and assembling text !!!
        with tracer.start_as_current_span("solve_puzzle") as span:
            self.logger.info("Starting puzzle solving")
            start_time = time.time()

            try:
                batch_result = await self.fragment_service.discover_fragments()
                elapsed = time.time() - start_time

                if not batch_result.fragments:
                    self.logger.warning("No fragments found")
                    return self._create_error_result("No fragments found", elapsed)

                self.logger.info("Assembling puzzle text", fragment_count=len(batch_result.fragments))
                puzzle_text = self._assemble_puzzle_text(batch_result.fragments, stream_threshold)
                stats = self._create_success_stats(batch_result, elapsed)

                span.set_attribute("puzzle_solved", True)
                span.set_attribute("elapsed_seconds", elapsed)
                span.set_attribute("fragment_count", len(batch_result.fragments))

                self.logger.info(
                    "Puzzle solved successfully",
                    elapsed=f"{elapsed:.3f}s",
                    completion_rate=f"{stats.completion_rate:.1%}"
                )
                return PuzzleResult(puzzle_text=puzzle_text, elapsed_seconds=elapsed, stats=stats)

            except Exception as e:
                # guardrail: Handle puzzle solving failures and return error result
                elapsed = time.time() - start_time
                span.set_attribute("puzzle_solved", False)
                span.set_attribute("error", str(e))
                self.logger.error("Failed to solve puzzle", error=str(e), elapsed=f"{elapsed:.3f}s")
                return self._create_error_result(f"Failed to solve puzzle: {str(e)}", elapsed)

    def _assemble_puzzle_text(self, fragments: list,
                              stream_threshold: int | None = None) -> str:  # Assemble puzzle text with optional streaming for large datasets !!!
        threshold = stream_threshold or self.config.stream_threshold

        if len(fragments) > threshold:
            return self._assemble_text_streaming(fragments)

        fragments_dict = {f.index: f.text for f in fragments}
        indices = sorted(fragments_dict.keys())
        return ' '.join(fragments_dict[idx] for idx in indices)

    def _assemble_text_streaming(self,
                                 fragments: list) -> str:  # Assemble text using streaming to reduce memory usage for large fragment sets !!!
        self.logger.debug("Using streaming assembly", fragment_count=len(fragments))
        indices = sorted(f.index for f in fragments)
        fragment_map = {f.index: f.text for f in fragments}

        result_parts = []
        for i in range(0, len(indices), self.config.chunk_size):
            chunk_text = ' '.join(fragment_map[idx] for idx in indices[i:i + self.config.chunk_size])
            result_parts.append(chunk_text)

        return ' '.join(result_parts)

    def _create_success_stats(self, batch_result: FragmentBatch,
                              elapsed: float) -> PuzzleStats:  # Create comprehensive statistics for successful puzzle solving !!!
        total_expected = batch_result.total_found + len(batch_result.missing_indices)
        completion_rate = batch_result.total_found / total_expected if total_expected > 0 else 0.0

        return PuzzleStats(
            total_found=batch_result.total_found,
            missing_count=len(batch_result.missing_indices),
            completion_rate=completion_rate,
            time_elapsed=elapsed,
            fragments_per_second=batch_result.total_found / elapsed if elapsed > 0 else 0,
            missing_indices=batch_result.missing_indices[:10],
            is_complete=batch_result.is_complete,
            completion_percentage=batch_result.completion_percentage,
            total_requests=self.fragment_service.successful_requests
        )

    @staticmethod
    def _create_error_result(error_message: str,
                             elapsed: float) -> PuzzleResult:  # Create error result with empty stats for failed puzzle solving !!!
        error_stats = PuzzleStats(
            total_found=0,
            missing_count=0,
            completion_rate=0.0,
            time_elapsed=elapsed,
            fragments_per_second=0.0,
            missing_indices=[],
            is_complete=False,
            completion_percentage=0.0,
            total_requests=0
        )
        return PuzzleResult(puzzle_text="", elapsed_seconds=elapsed, stats=error_stats)
