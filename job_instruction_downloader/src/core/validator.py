"""
Document validation functionality.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List


class DocumentValidator:
    """Validates downloaded documents."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the validator.

        Args:
            config: Validation configuration dictionary.
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

    def validate_file(self, file_path: str, validation_config: Dict[str, Any]) -> bool:
        """Validate a downloaded file.

        Args:
            file_path: Path to the file to validate.
            validation_config: Validation configuration.

        Returns:
            True if file is valid, False otherwise.
        """
        try:
            path = Path(file_path)

            if not path.exists():
                self.logger.error(f"File does not exist: {file_path}")
                return False

            file_size = path.stat().st_size
            min_size = validation_config.get("min_size", 0)
            max_size = validation_config.get("max_size", float('inf'))

            if file_size < min_size:
                self.logger.error(f"File too small: {file_size} < {min_size}")
                return False

            if file_size > max_size:
                self.logger.error(f"File too large: {file_size} > {max_size}")
                return False

            expected_types = validation_config.get("expected_file_types", [])
            if expected_types and path.suffix.lower() not in expected_types:
                self.logger.error(f"Invalid file type: {path.suffix}")
                return False

            if validation_config.get("check_content", False):
                return self._validate_content(file_path)

            return True

        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            return False

    def _validate_content(self, file_path: str) -> bool:
        """Validate document content.

        Args:
            file_path: Path to the file to validate.

        Returns:
            True if content is valid, False otherwise.
        """
        try:
            path = Path(file_path)

            if path.suffix.lower() in [".docx", ".doc"]:
                with open(file_path, 'rb') as f:
                    header = f.read(8)
                    if path.suffix.lower() == ".docx":
                        return header.startswith(b'PK')
                    elif path.suffix.lower() == ".doc":
                        return header.startswith(b'\xd0\xcf\x11\xe0')

            elif path.suffix.lower() == ".pdf":
                with open(file_path, 'rb') as f:
                    header = f.read(4)
                    return header == b'%PDF'

            return True

        except Exception as e:
            self.logger.warning(f"Content validation failed for {file_path}: {e}")
            return False

    def validate_document_structure(self, file_path: str) -> Dict[str, Any]:
        """Validate document structure and extract metadata.

        Args:
            file_path: Path to the file to validate.

        Returns:
            Dictionary with validation results and metadata.
        """
        result: Dict[str, Any] = {
            "valid": False,
            "file_size": 0,
            "file_type": "",
            "errors": [],
            "metadata": {}
        }
        errors: List[str] = result["errors"]

        try:
            path = Path(file_path)

            if not path.exists():
                errors.append("File does not exist")
                return result

            result["file_size"] = path.stat().st_size
            result["file_type"] = path.suffix.lower()

            if self._validate_content(file_path):
                result["valid"] = True
                result["metadata"] = self._extract_metadata(file_path)
            else:
                errors.append("Invalid file content")

        except Exception as e:
            errors.append(f"Validation error: {e}")

        return result

    def _extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from document.

        Args:
            file_path: Path to the file.

        Returns:
            Dictionary with extracted metadata.
        """
        metadata = {}

        try:
            path = Path(file_path)
            stat = path.stat()

            metadata.update({
                "file_name": path.name,
                "file_size": stat.st_size,
                "created_time": stat.st_ctime,
                "modified_time": stat.st_mtime,
                "file_extension": path.suffix.lower()
            })

        except Exception as e:
            self.logger.warning(f"Failed to extract metadata from {file_path}: {e}")

        return metadata
