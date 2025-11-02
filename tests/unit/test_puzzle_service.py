from unittest.mock import AsyncMock

import pytest

from puzzle_solver.config.settings import PuzzleServiceConfig
from puzzle_solver.domain.models.fragment import Fragment, FragmentBatch
from puzzle_solver.domain.services.puzzle import PuzzleService


@pytest.fixture
def mock_fragment_service():
    service = AsyncMock()
    service.successful_requests = 5
    return service


@pytest.fixture
def puzzle_config():
    return PuzzleServiceConfig(stream_threshold=3, chunk_size=2)


@pytest.fixture
def sample_fragments():
    return [
        Fragment(id=1, index=0, text="Hello"),
        Fragment(id=2, index=1, text="world"),
        Fragment(id=3, index=2, text="test")
    ]


class TestPuzzleService:
    def test_initialization(self, mock_fragment_service, puzzle_config):
        service = PuzzleService(mock_fragment_service, puzzle_config)
        assert service.fragment_service == mock_fragment_service
        assert service.config == puzzle_config

    @pytest.mark.asyncio
    async def test_solve_puzzle_success(self, mock_fragment_service, puzzle_config, sample_fragments):
        batch = FragmentBatch(fragments=sample_fragments, total_found=3, missing_indices=[])
        mock_fragment_service.discover_fragments.return_value = batch

        service = PuzzleService(mock_fragment_service, puzzle_config)
        text, elapsed, stats = await service.solve_puzzle()

        assert text == "Hello world test"
        assert elapsed > 0
        assert stats["total_fragments"] == 3
        assert stats["is_complete"] is True

    @pytest.mark.asyncio
    async def test_solve_puzzle_no_fragments(self, mock_fragment_service, puzzle_config):
        batch = FragmentBatch(fragments=[], total_found=0, missing_indices=[])
        mock_fragment_service.discover_fragments.return_value = batch

        service = PuzzleService(mock_fragment_service, puzzle_config)
        text, elapsed, stats = await service.solve_puzzle()

        assert text == ""
        assert "error" in stats
        assert stats["error"] == "No fragments found"

    @pytest.mark.asyncio
    async def test_solve_puzzle_exception(self, mock_fragment_service, puzzle_config):
        mock_fragment_service.discover_fragments.side_effect = Exception("Test error")

        service = PuzzleService(mock_fragment_service, puzzle_config)
        text, elapsed, stats = await service.solve_puzzle()

        assert text == ""
        assert "error" in stats
        assert "Test error" in stats["error"]

    def test_assemble_puzzle_text_normal(self, mock_fragment_service, puzzle_config, sample_fragments):
        service = PuzzleService(mock_fragment_service, puzzle_config)
        text = service._assemble_puzzle_text(sample_fragments[:2])  # Below threshold
        assert text == "Hello world"

    def test_assemble_puzzle_text_streaming(self, mock_fragment_service, puzzle_config, sample_fragments):
        service = PuzzleService(mock_fragment_service, puzzle_config)
        text = service._assemble_puzzle_text(sample_fragments)  # Above threshold (3)
        assert text == "Hello world test"

    def test_create_success_stats(self, mock_fragment_service, puzzle_config, sample_fragments):
        batch = FragmentBatch(fragments=sample_fragments, total_found=3, missing_indices=[])
        service = PuzzleService(mock_fragment_service, puzzle_config)

        stats = service._create_success_stats(batch, 1.5)

        assert stats["total_fragments"] == 3
        assert stats["missing_fragments"] == 0
        assert stats["completion_rate"] == 1.0
        assert stats["time_elapsed"] == 1.5
        assert stats["fragments_per_second"] == 2.0

    def test_create_error_stats(self, mock_fragment_service, puzzle_config):
        service = PuzzleService(mock_fragment_service, puzzle_config)
        stats = service._create_error_stats("Test error", 1.0)

        assert stats["error"] == "Test error"
        assert stats["time_elapsed"] == 1.0
