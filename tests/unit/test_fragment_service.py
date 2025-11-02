from unittest.mock import AsyncMock

import pytest

from puzzle_solver.config.settings import FragmentServiceConfig
from puzzle_solver.domain.models.fragment import Fragment
from puzzle_solver.domain.services.fragment import FragmentService


@pytest.fixture
def fragment_config():
    return FragmentServiceConfig(base_url="https://test.com", endpoint="/fragment", initial_batch_size=5)


@pytest.fixture
def sample_fragments():
    return [
        Fragment(id=1, index=0, text="Hello"),
        Fragment(id=2, index=1, text="world"),
        Fragment(id=3, index=3, text="test"),  # Missing index 2
    ]


class TestFragmentService:
    def test_initialization(self, fragment_config):
        service = FragmentService(fragment_config)
        assert service.config == fragment_config
        assert service.base_url == "https://test.com/fragment"

    def test_parse_response_valid(self, fragment_config):
        service = FragmentService(fragment_config)
        data = {"id": 1, "index": 0, "text": "Hello"}
        fragment = service.parse_response(data)

        assert fragment is not None
        assert fragment.id == 1
        assert fragment.text == "Hello"

    def test_parse_response_invalid(self, fragment_config):
        service = FragmentService(fragment_config)
        data = {"invalid": "data"}
        fragment = service.parse_response(data)

        assert fragment is None

    def test_build_url(self, fragment_config):
        service = FragmentService(fragment_config)
        url = service.build_url(123)
        assert url == "https://test.com/fragment?id=123"

    @pytest.mark.asyncio
    async def test_get_fragment(self, fragment_config):
        service = FragmentService(fragment_config)
        service.fetch_single = AsyncMock(return_value=Fragment(id=1, index=0, text="Hello"))

        fragment = await service.get_fragment(1)

        assert fragment.id == 1
        service.fetch_single.assert_called_once_with(fragment_id=1)

    @pytest.mark.asyncio
    async def test_get_fragments_batch(self, fragment_config, sample_fragments):
        service = FragmentService(fragment_config)
        service.fetch_batch = AsyncMock(return_value=sample_fragments)

        batch = await service.get_fragments_batch([1, 2, 3])

        assert batch.total_found == 3
        assert len(batch.missing_indices) == 1  # Missing index 2

    @pytest.mark.asyncio
    async def test_get_fragment_range(self, fragment_config, sample_fragments):
        service = FragmentService(fragment_config)
        service.fetch_batch = AsyncMock(return_value=sample_fragments)

        fragments = await service.get_fragment_range(1, 3)

        assert len(fragments) == 3
        service.fetch_batch.assert_called_once()

    @pytest.mark.asyncio
    async def test_discover_fragments(self, fragment_config):
        service = FragmentService(fragment_config)
        # Create complete fragments without missing indices to avoid infinite loop
        complete_fragments = [
            Fragment(id=1, index=0, text="Hello"),
            Fragment(id=2, index=1, text="world"),
            Fragment(id=3, index=2, text="test"),
        ]
        service.fetch_batch = AsyncMock(return_value=complete_fragments)

        batch = await service.discover_fragments()

        assert batch.total_found == 3
        assert len(batch.missing_indices) == 0
        assert batch.is_complete is True
        assert service.fetch_batch.call_count == 4  # 4 ranges

    @pytest.mark.asyncio
    async def test_discover_fragments_with_missing(self, fragment_config, sample_fragments):
        service = FragmentService(fragment_config)
        # First call returns fragments with missing index 2
        # Second call returns the missing fragment
        missing_fragment = Fragment(id=4, index=2, text="missing")
        service.fetch_batch = AsyncMock(
            side_effect=[
                sample_fragments,  # Initial discovery
                sample_fragments,  # Range 2
                sample_fragments,  # Range 3
                sample_fragments,  # Range 4
                [missing_fragment],  # Missing fragment fetch
            ]
        )

        batch = await service.discover_fragments()

        assert batch.total_found == 4  # 3 original + 1 missing
        assert len(batch.missing_indices) == 0
        assert batch.is_complete is True
        assert service.fetch_batch.call_count == 5  # 4 ranges + 1 missing fetch

    def test_generate_discovery_ranges(self, fragment_config):
        service = FragmentService(fragment_config)
        ranges = service._generate_discovery_ranges(10)

        expected = [(1, 10), (11, 20), (21, 30), (31, 40)]
        assert ranges == expected

    def test_collect_valid_fragments(self, fragment_config, sample_fragments):
        service = FragmentService(fragment_config)
        range_results = [sample_fragments[:2], Exception("error"), sample_fragments[2:]]

        fragments = service._collect_valid_fragments(range_results)

        assert len(fragments) == 3

    def test_create_fragment_batch_empty(self, fragment_config):
        service = FragmentService(fragment_config)
        batch = service._create_fragment_batch([])

        assert batch.total_found == 0
        assert batch.fragments == []
        assert batch.missing_indices == []

    def test_create_fragment_batch_with_fragments(self, fragment_config, sample_fragments):
        service = FragmentService(fragment_config)
        batch = service._create_fragment_batch(sample_fragments)

        assert batch.total_found == 3
        assert len(batch.missing_indices) == 1  # Missing index 2
