"""
Data model for job instruction documents.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


@dataclass
class JobInstruction:
    """Represents a job instruction document."""

    title: str
    department: str
    url: str
    file_path: Optional[Path] = None
    file_size: Optional[int] = None
    download_date: Optional[datetime] = None
    status: str = "pending"  # pending, downloading, completed, failed
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Post-initialization processing."""
        if self.metadata is None:
            self.metadata = {}

        if self.download_date is None and self.status == "completed":
            self.download_date = datetime.now()

    @property
    def filename(self) -> str:
        """Generate filename for the document."""
        clean_title = self.clean_filename(self.title)
        return f"{clean_title}.docx"

    @property
    def is_downloaded(self) -> bool:
        """Check if document is successfully downloaded."""
        return (
            self.status == "completed" and
            self.file_path is not None and
            self.file_path.exists()
        )

    def clean_filename(self, filename: str) -> str:
        """Clean filename by removing invalid characters."""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')

        filename = ' '.join(filename.split())
        if len(filename) > 100:
            filename = filename[:97] + "..."

        return filename

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "title": self.title,
            "department": self.department,
            "url": self.url,
            "file_path": str(self.file_path) if self.file_path else None,
            "file_size": self.file_size,
            "download_date": self.download_date.isoformat() if self.download_date else None,
            "status": self.status,
            "error_message": self.error_message,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobInstruction":
        """Create instance from dictionary."""
        download_date = None
        if data.get("download_date"):
            download_date = datetime.fromisoformat(data["download_date"])

        file_path = None
        if data.get("file_path"):
            file_path = Path(data["file_path"])

        return cls(
            title=data["title"],
            department=data["department"],
            url=data["url"],
            file_path=file_path,
            file_size=data.get("file_size"),
            download_date=download_date,
            status=data.get("status", "pending"),
            error_message=data.get("error_message"),
            metadata=data.get("metadata", {})
        )
