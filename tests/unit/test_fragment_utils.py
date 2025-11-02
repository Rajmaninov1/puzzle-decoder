import pytest

from puzzle_solver.domain.models.fragment import Fragment
from puzzle_solver.utils.fragment_utils import build_validated_url, find_fragment_bounds, estimate_id_for_index


class TestBuildValidatedUrl:
    def test_valid_fragment_id(self):
        url = build_validated_url("https://example.com", 123)
        assert url == "https://example.com?id=123"

    def test_zero_fragment_id(self):
        url = build_validated_url("https://example.com", 0)
        assert url == "https://example.com?id=0"

    def test_negative_fragment_id(self):
        with pytest.raises(ValueError, match="fragment_id must be a non-negative integer"):
            build_validated_url("https://example.com", -1)

    def test_non_integer_fragment_id(self):
        with pytest.raises(ValueError, match="fragment_id must be a non-negative integer"):
            build_validated_url("https://example.com", "123")  # noqa


class TestFindFragmentBounds:
    def test_empty_fragments(self):
        unique, missing = find_fragment_bounds([])
        assert unique == []
        assert missing == []

    def test_no_missing_fragments(self):
        fragments = [Fragment(id=1, index=0, text="A"), Fragment(id=2, index=1, text="B")]
        unique, missing = find_fragment_bounds(fragments)
        assert len(unique) == 2
        assert missing == []

    def test_missing_fragments(self):
        fragments = [Fragment(id=1, index=0, text="A"), Fragment(id=3, index=2, text="C")]
        unique, missing = find_fragment_bounds(fragments)
        assert len(unique) == 2
        assert missing == [1]

    def test_duplicate_fragments(self):
        fragments = [Fragment(id=1, index=0, text="A"), Fragment(id=1, index=0, text="A")]
        unique, missing = find_fragment_bounds(fragments)
        assert len(unique) == 1
        assert missing == []


class TestEstimateIdForIndex:
    def test_insufficient_samples(self):
        fragments = [Fragment(id=10, index=0, text="A")]
        result = estimate_id_for_index(5, fragments)
        assert result == 5

    def test_same_index_samples(self):
        fragments = [Fragment(id=10, index=0, text="A"), Fragment(id=10, index=0, text="A")]
        result = estimate_id_for_index(5, fragments)
        assert result == 10

    def test_linear_estimation(self):
        fragments = [Fragment(id=10, index=0, text="A"), Fragment(id=20, index=10, text="B")]
        result = estimate_id_for_index(5, fragments)
        assert result == 15
