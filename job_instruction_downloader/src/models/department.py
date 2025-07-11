"""
Data model for department information.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .job_instruction import JobInstruction


@dataclass
class Department:
    """Represents a department with job instructions."""

    id: str
    name: str
    folder_name: str
    priority: int = 1
    enabled: bool = True
    job_instructions: Optional[List["JobInstruction"]] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Post-initialization processing."""
        if self.job_instructions is None:
            self.job_instructions = []

        if self.metadata is None:
            self.metadata = {}

    @property
    def total_documents(self) -> int:
        """Get total number of documents in department."""
        return len(self.job_instructions) if self.job_instructions else 0

    @property
    def completed_documents(self) -> int:
        """Get number of completed downloads."""
        if not self.job_instructions:
            return 0
        return sum(1 for ji in self.job_instructions if ji.status == "completed")

    @property
    def failed_documents(self) -> int:
        """Get number of failed downloads."""
        if not self.job_instructions:
            return 0
        return sum(1 for ji in self.job_instructions if ji.status == "failed")

    @property
    def progress_percentage(self) -> float:
        """Get download progress as percentage."""
        if self.total_documents == 0:
            return 0.0
        return (self.completed_documents / self.total_documents) * 100

    def add_job_instruction(self, job_instruction: "JobInstruction") -> None:
        """Add a job instruction to this department."""
        if self.job_instructions is None:
            self.job_instructions = []
        self.job_instructions.append(job_instruction)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "folder_name": self.folder_name,
            "priority": self.priority,
            "enabled": self.enabled,
            "job_instructions": [ji.to_dict() for ji in self.job_instructions] if self.job_instructions else [],
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Department":
        """Create instance from dictionary."""
        from .job_instruction import JobInstruction

        job_instructions = []
        if data.get("job_instructions"):
            job_instructions = [JobInstruction.from_dict(ji_data) for ji_data in data["job_instructions"]]

        return cls(
            id=data["id"],
            name=data["name"],
            folder_name=data["folder_name"],
            priority=data.get("priority", 1),
            enabled=data.get("enabled", True),
            job_instructions=job_instructions,
            metadata=data.get("metadata", {})
        )
