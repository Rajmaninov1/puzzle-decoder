from puzzle_solver.domain.models.fragment import Fragment


def build_validated_url(base_url: str, fragment_id: int) -> str:
    """Build fragment URL with validation."""
    if not isinstance(fragment_id, int) or fragment_id < 0:
        raise ValueError("fragment_id must be a non-negative integer")
    return f"{base_url}?id={fragment_id}"


def find_fragment_bounds(fragments: list[Fragment]) -> tuple[list[Fragment], list[int]]:
    """Remove duplicates and find missing indices."""
    fragments_by_index = {f.index: f for f in fragments}
    unique_fragments = list(fragments_by_index.values())
    indices = list(fragments_by_index.keys())

    if not indices:
        return unique_fragments, []

    min_idx, max_idx = min(indices), max(indices)
    missing_indices = [i for i in range(min_idx, max_idx + 1) if i not in fragments_by_index]

    return unique_fragments, missing_indices


def estimate_id_for_index(target_index: int, sample_fragments: list[Fragment]) -> int:
    """Estimate fragment ID for given index based on sample."""
    if len(sample_fragments) < 2:
        return target_index

    sample_fragments.sort(key=lambda f: f.index)
    first, last = sample_fragments[0], sample_fragments[-1]

    if last.index == first.index:
        return first.id

    ratio = (last.id - first.id) / (last.index - first.index)
    return int(first.id + (target_index - first.index) * ratio)
