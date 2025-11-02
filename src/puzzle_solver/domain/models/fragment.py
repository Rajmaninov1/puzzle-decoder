from pydantic import BaseModel, Field


class Fragment(BaseModel):
    """Single puzzle fragment."""
    id: int = Field(..., description="Unique fragment identifier")
    index: int = Field(..., description="Position in the puzzle sequence")
    text: str = Field(..., description="Fragment content")

    def __str__(self) -> str:
        """String representation."""
        return f"Fragment({self.id}, idx={self.index}, text='{self.text[:20]}...')" if len(
            self.text) > 20 else f"Fragment({self.id}, idx={self.index}, text='{self.text}')"


class FragmentBatch(BaseModel):
    """Fragment collection with metadata."""
    fragments: list[Fragment] = Field(default_factory=list)
    total_found: int = Field(0, description="Number of fragments found")
    missing_indices: list[int] = Field(default_factory=list, description="Indices of missing fragments")

    @property
    def is_complete(self) -> bool:
        """Check if all fragments are present."""
        return len(self.missing_indices) == 0

    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        total_expected = self.total_found + len(self.missing_indices)
        return (self.total_found / total_expected * 100) if total_expected > 0 else 0.0
