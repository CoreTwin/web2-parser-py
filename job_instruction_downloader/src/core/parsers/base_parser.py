"""
Base parser class for universal document extraction.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from selenium import webdriver

from ...models.job_instruction import JobInstruction
from ...models.department import Department


class BaseParser(ABC):
    """Base class for all site parsers."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the parser.

        Args:
            config: Site configuration dictionary.
        """
        self.config = config
        self.site_config = config.get("site_config", {})

    @abstractmethod
    def extract_documents(self, driver: webdriver.Chrome, department: Department) -> List[JobInstruction]:
        """Extract job instruction documents for a department.

        Args:
            driver: Selenium WebDriver instance.
            department: Department to extract documents for.

        Returns:
            List of extracted job instructions.
        """
        pass

    @abstractmethod
    def validate_document(self, file_path: str) -> bool:
        """Validate downloaded document.

        Args:
            file_path: Path to the downloaded file.

        Returns:
            True if document is valid, False otherwise.
        """
        pass

    def get_selectors(self) -> Dict[str, str]:
        """Get CSS selectors for document extraction.

        Returns:
            Dictionary of CSS selectors.
        """
        return self.site_config.get("extraction", {}).get("selectors", {})

    def get_rate_limits(self) -> Dict[str, Any]:
        """Get rate limiting configuration.

        Returns:
            Rate limiting configuration dictionary.
        """
        return self.site_config.get("rate_limiting", {})

    def get_download_config(self) -> Dict[str, Any]:
        """Get download configuration.

        Returns:
            Download configuration dictionary.
        """
        return self.site_config.get("download", {})

    def get_validation_config(self) -> Dict[str, Any]:
        """Get validation configuration.

        Returns:
            Validation configuration dictionary.
        """
        return self.get_download_config().get("validation", {})

    def process_title(self, title: str) -> str:
        """Process and clean document title.

        Args:
            title: Raw document title.

        Returns:
            Cleaned title.
        """
        if not title:
            return ""

        title_config = self.site_config.get("extraction", {}).get("title_processing", {})

        remove_prefixes = title_config.get("remove_prefixes", [])
        for prefix in remove_prefixes:
            if title.startswith(prefix):
                title = title[len(prefix):].strip()

        remove_suffixes = title_config.get("remove_suffixes", [])
        for suffix in remove_suffixes:
            if title.endswith(suffix):
                title = title[:-len(suffix)].strip()

        max_length = title_config.get("max_length", 100)
        if len(title) > max_length:
            title = title[:max_length].strip()

        cleanup_regex = title_config.get("cleanup_regex", r"\s+")
        replacement = title_config.get("replacement", " ")
        if cleanup_regex:
            import re
            title = re.sub(cleanup_regex, replacement, title)

        return title.strip()
