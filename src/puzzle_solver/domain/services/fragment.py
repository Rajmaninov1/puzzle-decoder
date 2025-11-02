import asyncio
from typing import Any

import structlog
from pydantic import ValidationError

from puzzle_solver.config.settings import FragmentServiceConfig
from puzzle_solver.core.observability import fragment_counter, tracer
from puzzle_solver.domain.models.fragment import Fragment, FragmentBatch
from puzzle_solver.domain.services.base import BaseWebService
from puzzle_solver.utils.fragment_utils import build_validated_url, find_fragment_bounds


class FragmentService(BaseWebService[Fragment]):
    """Service for fetching puzzle fragments."""

    def __init__(
        self, config: FragmentServiceConfig | None = None
    ) -> None:  # Initialize fragment service with configuration and HTTP client setup !!!
        self.config = config or FragmentServiceConfig()
        self.logger = structlog.get_logger()
        super().__init__(
            base_url=self.config.full_url,
            max_concurrent=self.config.max_concurrent,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
        )
        self.logger.info(
            "FragmentService initialized", base_url=self.config.base_url, max_concurrent=self.config.max_concurrent
        )

    def parse_response(
        self, data: dict[str, Any]
    ) -> Fragment | None:  # Parse JSON response data to Fragment model with validation !!!
        try:
            return Fragment(**data)
        except ValidationError as e:
            # guardrail: Handle invalid fragment data gracefully
            self.logger.warning("Invalid fragment data", error=str(e))
            return None

    def build_url(self, fragment_id: int) -> str:  # Build validated fragment URL with ID parameter !!!
        return build_validated_url(self.base_url, fragment_id)

    async def test_connectivity(self) -> None:  # Test connectivity to fragment service by fetching single fragment !!!
        await self.fetch_single(fragment_id=1)

    async def get_fragment(
        self, fragment_id: int
    ) -> Fragment | None:  # Get single fragment by ID with error handling !!!
        return await self.fetch_single(fragment_id=fragment_id)

    async def get_fragments_batch(
        self, fragment_ids: list[int]
    ) -> FragmentBatch:  # Get multiple fragments with statistics for testing purposes !!!
        param_list = [{"fragment_id": fid} for fid in fragment_ids]
        fragments = await self.fetch_batch(param_list)
        return self._create_fragment_batch(fragments)

    async def get_fragment_range(
        self, start_id: int, count: int
    ) -> list[Fragment]:  # Get range of fragments by consecutive IDs for batch processing !!!
        return await self.fetch_range(start=start_id, count=count, param_builder=lambda i: {"fragment_id": i})

    async def _fetch_missing_fragments(
        self, missing_indices: list[int]
    ) -> list[Fragment]:  # Fetch fragments for missing indices to complete puzzle !!!
        param_list = [{"fragment_id": idx} for idx in missing_indices]
        return await self.fetch_batch(param_list)

    async def discover_fragments(
        self, initial_batch_size: int | None = None
    ) -> FragmentBatch:  # Discover all puzzle fragments with maximum parallelism and gap detection !!!
        with tracer.start_as_current_span("discover_fragments") as span:
            batch_size = initial_batch_size or self.config.initial_batch_size
            span.set_attribute("batch_size", batch_size)
            self.logger.info("Starting fragment discovery", batch_size=batch_size)

            ranges = self._generate_discovery_ranges(batch_size)
            self.logger.debug("Generated discovery ranges", ranges=ranges)

            tasks = [self.get_fragment_range(start, end - start + 1) for start, end in ranges]
            range_results = await asyncio.gather(*tasks, return_exceptions=True)

            all_fragments = self._collect_valid_fragments(range_results)
            batch = self._create_fragment_batch(all_fragments)

            # Search for missing fragments until complete
            while batch.missing_indices:
                self.logger.info("Searching for missing fragments", missing_count=len(batch.missing_indices))
                missing_fragments = await self._fetch_missing_fragments(batch.missing_indices)
                all_fragments.extend(missing_fragments)
                batch = self._create_fragment_batch(all_fragments)

            # Update metrics
            fragment_counter.labels(status="found").inc(batch.total_found)
            fragment_counter.labels(status="missing").inc(len(batch.missing_indices))

            span.set_attribute("fragments_found", batch.total_found)
            span.set_attribute("fragments_missing", len(batch.missing_indices))

            self.logger.info(
                "Fragment discovery completed",
                total_found=batch.total_found,
                missing_count=len(batch.missing_indices),
                completion_rate=f"{batch.completion_percentage:.1f}%",
            )
            return batch

    @staticmethod
    def _generate_discovery_ranges(
        batch_size: int,
    ) -> list[tuple[int, int]]:  # Generate discovery ranges for parallel fragment fetching optimization !!!
        return [
            (1, batch_size),
            (batch_size + 1, batch_size * 2),
            (batch_size * 2 + 1, batch_size * 3),
            (batch_size * 3 + 1, batch_size * 4),
        ]

    @staticmethod
    def _collect_valid_fragments(
        range_results: list,
    ) -> list[Fragment]:  # Collect valid fragments from range results filtering exceptions !!!
        all_fragments = []
        for result in range_results:
            if isinstance(result, list):
                all_fragments.extend(result)
        return all_fragments

    @staticmethod
    def _create_fragment_batch(
        fragments: list[Fragment],
    ) -> FragmentBatch:  # Create FragmentBatch with statistics and missing indices detection !!!
        if not fragments:
            return FragmentBatch(fragments=[], total_found=0, missing_indices=[])

        unique_fragments, missing_indices = find_fragment_bounds(fragments)
        return FragmentBatch(
            fragments=unique_fragments, total_found=len(unique_fragments), missing_indices=missing_indices
        )
