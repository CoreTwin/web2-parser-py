"""
Base resource adapter for universal document processing.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path

from ...models.job_instruction import JobInstruction
from ...models.department import Department


class BaseResourceAdapter(ABC):
    """Base interface for all document resource adapters."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the resource adapter.

        Args:
            config: Configuration dictionary for the adapter.
        """
        self.config = config
        self.site_config = config.get("site_config", {})

    @abstractmethod
    def authenticate(self, credentials: Optional[Dict[str, Any]] = None) -> bool:
        """Authenticate with the resource.

        Args:
            credentials: Authentication credentials.

        Returns:
            True if authentication successful, False otherwise.
        """
        pass

    @abstractmethod
    def get_document_list(self, department: Department, filters: Optional[Dict[str, Any]] = None) -> List[JobInstruction]:
        """Get list of documents from the resource.

        Args:
            department: Department to get documents for.
            filters: Optional filters to apply.

        Returns:
            List of available documents.
        """
        pass

    @abstractmethod
    def download_document(self, document: JobInstruction, download_path: Path) -> bool:
        """Download a document from the resource.

        Args:
            document: Document to download.
            download_path: Path to save the document.

        Returns:
            True if download successful, False otherwise.
        """
        pass

    @abstractmethod
    def validate_document(self, file_path: Path) -> bool:
        """Validate a downloaded document.

        Args:
            file_path: Path to the downloaded file.

        Returns:
            True if document is valid, False otherwise.
        """
        pass

    @abstractmethod
    def get_metadata(self, document: JobInstruction) -> Dict[str, Any]:
        """Get metadata for a document.

        Args:
            document: Document to get metadata for.

        Returns:
            Dictionary containing document metadata.
        """
        pass

    def get_rate_limits(self) -> Dict[str, Any]:
        """Get rate limiting configuration.

        Returns:
            Rate limiting configuration dictionary.
        """
        rate_limits = self.site_config.get("rate_limiting", {})
        return rate_limits if isinstance(rate_limits, dict) else {}

    def get_download_config(self) -> Dict[str, Any]:
        """Get download configuration.

        Returns:
            Download configuration dictionary.
        """
        download_config = self.site_config.get("download", {})
        return download_config if isinstance(download_config, dict) else {}

    def get_validation_config(self) -> Dict[str, Any]:
        """Get validation configuration.

        Returns:
            Validation configuration dictionary.
        """
        validation_config = self.get_download_config().get("validation", {})
        return validation_config if isinstance(validation_config, dict) else {}
